# Research Article Summarizer

A small AI-assisted research workflow for students: upload a spreadsheet of article links, generate consistent summaries, and download a shareable document.

## Workflow

`CSV/XLSX → article text → AI summary → Markdown/HTML export`

### Summary structure

Every article follows the same format:

- **Article Title**
- **Main Idea**
- **Supporting Points**
- **Key Takeaways**
- **Evidence / Caveats**
- **Source URL**

The prompt explicitly tells the model not to invent facts and to distinguish claims from evidence.

## Test dataset

`data/articles.csv` contains three synthetic reading records. The URLs use `sample://`, and `data/sample_content.json` contains the matching article text. This makes it possible to test the complete workflow without depending on external websites.

## Run locally

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
streamlit run app.py
```

Optional: set `OPENAI_MODEL` to another compatible OpenAI model.

## Input format

Required columns:

```text
title,url
```

Optional column:

```text
notes
```

## Export

The app produces Markdown and a clean HTML document. The HTML file is suitable for sharing and can be copied into Google Docs when a Google account integration is not available.

## Privacy

Article text is sent to the configured AI provider only when summarization is requested. Do not use sensitive material unless the chosen provider/account is approved for it.

## Project structure

```text
.
├── app.py
├── data/
│   ├── articles.csv
│   └── sample_content.json
├── requirements.txt
└── README.md
```
