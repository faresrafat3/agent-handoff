# Regenerate the committed demo assets. The image is never hand-edited — if the
# tool's behaviour changes, re-run this and the picture follows.
.PHONY: demo image verify

demo:
	./demo.sh

image:
	python3 render_demo.py

verify: demo image
	cd .. && python3 -B -m unittest discover -s tests && python3 -B bin/agent-handoff conformance
