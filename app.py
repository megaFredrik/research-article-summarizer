import html
import json
import os
import re

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI

st.set_page_config(page_title="Research Article Summarizer", page_icon="📚", layout="wide")

SYSTEM_PROMPT = """You are a research assistant for students. Summarize the supplied article text faithfully and concisely. Never invent facts. Use exactly this structure:
Article Title:
Main Idea:
Supporting Points:
- point
- point
- point
Key Takeaways:
- takeaway
- takeaway
Evidence / Caveats:
- evidence or limitation
Source URL:
Keep language student-friendly. Distinguish claims from evidence and explicitly say when evidence is unclear or absent."""


def fetch_article(url: str) -> str:
    """Fetch readable article text, or deterministic local sample content."""
    url = url.strip()
    if url.startswith("sample://"):
        with open("data/sample_content.json", encoding="utf-8") as f:
            samples = json.load(f)
        if url not in samples:
            raise ValueError(f"Unknown sample URL: {url}")
        return samples[url]

    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        raise ValueError("URL must start with http:// or https://")

    headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchSummarizer/1.0)"}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = "\n".join(x.strip() for x in soup.stripped_strings)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text.strip():
        raise ValueError("No readable article text was found.")
    return text[:30000]


def summarize(title: str, url: str, text: str, notes: str = "") -> str:
    """Generate a consistent student-friendly summary with the configured model."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)
    user = f"Title: {title}\nURL: {url}\nStudent notes: {notes}\n\nARTICLE TEXT:\n{text}"
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user,
    )
    return response.output_text.strip()


def to_markdown(rows: list[dict]) -> str:
    out = ["# Research Reading Summaries", "", f"Generated: {pd.Timestamp.now().date()}", ""]
    for row in rows:
        out += ["---", "", row["summary"], ""]
    return "\n".join(out)


def to_html(rows: list[dict]) -> str:
    """Create a clean shareable HTML document that can be copied into Google Docs."""
    articles = []
    for row in rows:
        articles.append(
            "<article>"
            f"<h2>{html.escape(str(row['title']))}</h2>"
            f"<pre>{html.escape(row['summary'])}</pre>"
            "</article>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Research Reading Summaries</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;line-height:1.5}"
        "article{margin:0 0 32px}pre{white-space:pre-wrap;font-family:inherit}</style>"
        "</head><body><h1>Research Reading Summaries</h1>"
        + "".join(articles)
        + "</body></html>"
    )


st.title("📚 Research Article Summarizer")
st.caption("Spreadsheet links → consistent AI summaries → shareable download")

with st.sidebar:
    uploaded = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Set OPENAI_API_KEY before generating summaries.")
    st.markdown("Required: `title`, `url` · Optional: `notes`")
    st.markdown("Sample data uses `sample://` URLs, so it can be tested without external websites.")

if uploaded:
    df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
else:
    df = pd.read_csv("data/articles.csv")

required = {"title", "url"}
if not required.issubset(df.columns):
    st.error(f"The spreadsheet must contain: {', '.join(sorted(required))}")
    st.stop()

st.subheader("Reading list")
st.dataframe(df, use_container_width=True, hide_index=True)

if st.button("Generate summaries", type="primary", disabled=not bool(os.getenv("OPENAI_API_KEY"))):
    results = []
    progress = st.progress(0)
    for i, row in df.iterrows():
        try:
            title = str(row["title"])
            url = str(row["url"])
            notes = str(row.get("notes", ""))
            text = fetch_article(url)
            summary = summarize(title, url, text, notes)
            results.append({"title": title, "url": url, "summary": summary, "status": "OK"})
        except Exception as exc:
            results.append(
                {
                    "title": str(row["title"]),
                    "url": str(row["url"]),
                    "summary": f"ERROR: {exc}",
                    "status": "ERROR",
                }
            )
        progress.progress((i + 1) / len(df))
    st.session_state.results = results

if "results" in st.session_state:
    results = st.session_state.results
    st.subheader("Summaries")
    for row in results:
        with st.expander(f"{row['status']} — {row['title']}", expanded=True):
            st.markdown(row["summary"])

    st.download_button(
        "Download Markdown",
        to_markdown(results),
        "research-summaries.md",
        "text/markdown",
    )
    st.download_button(
        "Download shareable HTML / Google Docs-ready",
        to_html(results),
        "research-summaries.html",
        "text/html",
    )

st.divider()
st.caption(
    "Privacy: article text is sent to the configured AI provider only during summarization. "
    "Avoid sensitive content unless approved for that provider/account."
)
