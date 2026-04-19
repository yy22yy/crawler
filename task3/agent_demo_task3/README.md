# task3 Agent Demo

This folder contains a small plan-and-execute workflow orchestrator demo for task3.

## What it demonstrates

- Plan by city profile
- Prefer normal DOM extraction first
- Fall back to OCR when DOM extraction fails
- Fall back to LLM vision when OCR is insufficient
- Validate the extracted fields before finishing

## Why this is not a full Agent

This demo is intentionally a workflow orchestrator instead of a fully autonomous Agent:

- The path is predefined
- Fallback order is explicit
- Validation is rule-based
- LLM is only used when the pipeline needs a fallback

## Run

```bash
python workflow_orchestrator_demo.py
```

## How to map to the real project

- `plan_node` -> read `city_config.json` and page structure hints
- `try_dom_extract` -> reuse normal Selenium DOM extraction
- `try_ocr_extract` -> reuse `task3_tesseract.py`
- `try_llm_extract` -> reuse `task3_model.py`
- `check_fields` -> field completeness and format validation
