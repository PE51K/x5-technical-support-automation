# `scr` dir file explanations

```
├── settings.py               # All of the pydantic settings
├── ui.py                     # Gradio UI file
├── cli.py                    # CLI version (depricated)
├── workflow.py               # Workflow logic
├── workflow_events.py        # All of the workflow events
├── workflow_with_tracing.py  # Workflow wrapper for tracing
└── workflow_steps            # Steps for the workflow
    ├── preprocess.py
    ├── retrieve.py
    ├── deduplicate.py
    ├── sanity_check.py
    ├── qa_examples.py        
    └── reply.py
```