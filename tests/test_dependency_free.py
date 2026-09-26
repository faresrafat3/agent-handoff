"""Differential test: the built-in loader/validator against PyYAML + jsonschema.

Having no dependencies is the claim. *Agreeing* with the reference
implementations is the evidence. This test measures the second, on every record
the project ships plus deliberately malformed variants, and skips rather than
fakes a result when the reference packages are unavailable.

A test that skipped silently would be worse than no test, so the skip is
reported in the assertion message.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "agent-handoff"

try:
    import yaml as pyyaml
    import jsonschema as pyjsonschema
    REFERENCE = True
except ImportError:  # pragma: no cover
    pyyaml = pyjsonschema = None
    REFERENCE = False


def load_cli():
    namespace = {"__name__": "cli_under_test"}
    exec(compile(CLI.read_text(encoding="utf-8"), str(CLI), "exec"), namespace)
    return namespace


class DependencyFreeTests(unittest.TestCase):
    def setUp(self):
        self.cli = load_cli()

    def test_no_third_party_imports_in_the_tool(self):
        source = CLI.read_text(encoding="utf-8")
        for banned in ("import yaml", "import jsonschema", "yaml.safe_load", "jsonschema."):
            self.assertNotIn(banned, source, f"{banned} reintroduced a runtime dependency")

    def test_loader_agrees_with_pyyaml_on_every_shipped_record(self):
        if not REFERENCE:
            self.skipTest("PyYAML absent — the reference comparison could not run")
        records = sorted((ROOT / ".agent-workspace").rglob("*.yaml"))
        records += sorted((ROOT / ".agent-workspace").rglob("*.yml"))
        records += sorted((ROOT / "tests" / "fixtures").glob("*.md"))
        self.assertGreater(len(records), 3, "no records found to compare")
        for path in records:
            raw = path.read_text(encoding="utf-8")
            if path.suffix == ".md":
                # Extract the frontmatter block directly. The CLI's helper takes
                # a Path, and this test is about the loader, not about that
                # helper's file handling.
                import re as _re
                block = _re.match(r"^---\n(.*?)\n---\n", raw, _re.S)
                if not block:
                    continue
                raw = block.group(1)
            # Compare what the tool actually validates. PyYAML resolves an
            # ISO timestamp to `datetime`; the tool normalises that back to a
            # string before validating, because the schema says `type: string`.
            # Comparing raw parse trees would flag a difference the tool does
            # not care about, and would hide one it does.
            def normalize(value):
                """Reduce to the value the tool actually compares.

                Two things matter. First, PyYAML resolves an ISO timestamp to
                `datetime`; the tool normalises it back, because the schema says
                `type: string`. Second, `Z` and `+00:00` are the same instant
                written differently, so an instant-aware comparison is the honest
                one — comparing text would flag a formatting difference the tool
                does not care about while hiding one it does.
                """
                import datetime as _dt
                if isinstance(value, _dt.datetime):
                    return ("instant", value.astimezone(_dt.timezone.utc))
                if isinstance(value, _dt.date):
                    return ("date", value)
                if isinstance(value, str):
                    # A bare `YYYY-MM-DD` is a date to PyYAML but a string to the
                    # built-in loader. `datetime.fromisoformat` accepts it too, so
                    # the date-only shape has to be tested before the instant one
                    # or this branch is unreachable.
                    if len(value) == 10 and value[4] == "-" and value[7] == "-":
                        try:
                            return ("date", _dt.date.fromisoformat(value))
                        except ValueError:
                            return value
                    try:
                        parsed = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        return value
                    if parsed.tzinfo is not None:
                        return ("instant", parsed.astimezone(_dt.timezone.utc))
                    return value
                if isinstance(value, dict):
                    return {k: normalize(v) for k, v in value.items()}
                if isinstance(value, list):
                    return [normalize(v) for v in value]
                return value

            self.assertEqual(
                normalize(self.cli["yaml_load"](raw)),
                normalize(pyyaml.safe_load(raw)),
                f"loader disagrees with PyYAML on {path.relative_to(ROOT)}",
            )

    def test_validator_agrees_with_jsonschema_on_every_shipped_schema(self):
        if not REFERENCE:
            self.skipTest("jsonschema absent — the reference comparison could not run")
        cases = []
        for path in sorted((ROOT / "schemas").glob("*.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            cases.extend(self._instances_for(schema))

        self.assertGreater(len(cases), 20, "not enough instances to be meaningful")
        for schema, instance in cases:
            mine = bool(self.cli["_schema_errors"](schema, instance))
            theirs = not pyjsonschema.Draft202012Validator(schema).is_valid(instance)
            self.assertEqual(
                mine, theirs,
                f"verdict disagrees on {json.dumps(instance)[:120]}\n"
                f"  built-in: {mine}  jsonschema: {theirs}\n"
                f"  schema: {json.dumps(schema)[:200]}",
            )

    def _instances_for(self, schema, depth=0):
        """Generate valid and deliberately-invalid instances of a schema."""
        if depth > 4:
            return []
        out = []
        valid = self._minimal(schema)
        if valid is not _MISSING:
            out.append((schema, valid))
            # a wrong type
            out.append((schema, "definitely not the right type"))
            # an extra property, to exercise additionalProperties
            if isinstance(valid, dict):
                broken = dict(valid)
                broken["unexpected_field"] = 1
                out.append((schema, broken))
        for name, sub in (schema.get("properties") or {}).items():
            if isinstance(sub, dict):
                out.extend(self._instances_for(sub, depth + 1))
        return out

    def _minimal(self, schema):
        """Smallest instance that should satisfy `schema`, or _MISSING."""
        if "const" in schema:
            return schema["const"]
        if "enum" in schema:
            return schema["enum"][0]
        expected = schema.get("type")
        options = expected if isinstance(expected, list) else ([expected] if expected else [])
        if "object" in options:
            value = {}
            for name in schema.get("required", []):
                sub = (schema.get("properties") or {}).get(name)
                if isinstance(sub, dict):
                    child = self._minimal(sub)
                    if child is _MISSING:
                        return _MISSING
                    value[name] = child
            for name, sub in (schema.get("properties") or {}).items():
                if name not in value and isinstance(sub, dict):
                    child = self._minimal(sub)
                    if child is not _MISSING:
                        value[name] = child
            return value
        if "array" in options:
            return []
        if "string" in options:
            if "pattern" in schema:
                import re as _re
                match = _re.match(schema["pattern"], "x" * 200)
                if not match:
                    return _MISSING
                return match.group(0)
            if schema.get("format") == "uri":
                return "https://example.invalid/x"
            return "x" * max(1, schema.get("minLength", 1))
        if "integer" in options:
            return max(0, schema.get("minimum", 0))
        if "number" in options:
            return float(max(0, schema.get("minimum", 0)))
        if "boolean" in options:
            return False
        if "null" in options:
            return None
        return _MISSING


class _Missing:
    pass


_MISSING = _Missing()

if __name__ == "__main__":
    unittest.main()
