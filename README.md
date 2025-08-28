# Flipkart-ISCP-Real-time-PII-Defense

A minimal, to-the-point PII detection and redaction tool for structured data (CSV/JSON) using Python. Designed for real-time or batch processing of sensitive information such as names, phone numbers, Aadhar, passport, UPI, email, addresses, and more. Includes optional spaCy-based NER for unstructured fields.


## Setup

You can use either pip or [uv](https://github.com/astral-sh/uv) to install dependencies.

### Using pip
```sh
pip install -r requirements.txt  # or install from pyproject.toml if available
```

### Using uv (recommended for speed)
```sh
uv pip install -r requirements.txt  # or use uv pip install -r pyproject.toml
```

To enable spaCy-based NER, also run:
```sh
python -m spacy download en_core_web_sm
```

## Usage

- Place your input CSV in the project directory.
- Run:
  ```sh
  python detector_full_eeshaan_undar_bhat.py <input_csv>
  ```
- Output is written to `redacted_output_candidate_full_name.csv`.


## Features
- Regex-based detection and masking of common Indian PII fields
- Optional spaCy NER for unstructured text (if spaCy and `en_core_web_sm` are installed)
- Handles malformed JSON in input robustly

## Extra Python Modules Used
- spacy (optional, for NER)
- regex (re, built-in)
- csv, json, sys (built-in)

## Related Project
For a more advanced, universal, and AI-powered redaction service (covering text, PDFs, images, audio, and video), see my other project: [REDACT](https://github.com/SmartyDroidBot/RE-DACT)

## License
See LICENSE.md.
