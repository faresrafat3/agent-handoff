# tasks/

One directory per task, named `T-NNNN-slug`, each holding `task.yaml`,
`spec.md`, `plan.md`, `state.yaml`, `validation.md`, and `handoffs/`.

This README is versioned so the directory survives a clone. Git does not track
empty directories, and a required path that vanishes on a fresh checkout makes
`doctor --strict` fail on a workspace that is in fact correct — which trains
people to ignore the gate. That is the exact failure this project exists to
prevent, so the directory carries a file.
