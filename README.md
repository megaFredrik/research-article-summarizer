# Research Article Summarizer

AI-assisted research workflow for generating consistent, student-friendly article summaries from a spreadsheet of links.

## Workflow

1. Prepare `data/articles.csv` with `title,url,notes`.
2. Run the Streamlit app with an OpenAI API key.
3. The app extracts article text, generates a consistent summary, and lets you download Markdown/HTML.
4. Use the generated HTML as a shareable document or copy it into Google Docs.

## Structure

Every summary follows:
- Article Title
- Main Idea
- Supporting Points
- Key Takeaways
- Evidence / Caveats
- Source URL

## Privacy

The app sends article text to the configured AI provider only when summarization is requested. Do not upload sensitive material unless your chosen provider and account are approved for it.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Set `OPENAI_API_KEY` in your environment before running.

## Test data

See `data/articles.csv` for a small synthetic dataset designed to test parsing, consistency, and export.
