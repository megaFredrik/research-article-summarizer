import os
import re
import io
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import requests
from openai import OpenAI

st.set_page_config(page_title="Research Article Summarizer", page_icon="📚", layout="wide")

STRUCTURE = ["Article Title", "Main Idea", "Supporting Points", "Key Takeaways", "Evidence / Caveats", "Source URL"]

SYSTEM_PROMPT = """You are a research assistant for students. Summarize the supplied article text faithfully and concisely. Do not invent facts. Use exactly this structure:
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
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchSummarizer/1.0)"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = "\n".join(x.strip() for x in soup.stripped_strings)
    return re.sub(r"\n{3,}", "\n\n", text)[:30000]

def summarize(title, url, text, notes=""):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    user = f"Title: {title}\nURL: {url}\nStudent notes: {notes}\n\nARTICLE TEXT:\n{text}"
    response = client.responses.create(model="gpt-4.1-mini", instructions=SYSTEM_PROMPT, input=user)
    return response.output_text

def to_markdown(rows):
    out = ["# Research Reading Summaries", "", f"Generated: {pd.Timestamp.now().date()}", ""]
    for r in rows:
        out += ["---", "", r["summary"], ""]
    return "\n".join(out)

st.title("📚 Research Article Summarizer")
st.caption("Upload a spreadsheet of article links → generate consistent, student-friendly summaries → download a shareable document.")

with st.sidebar:
    st.header("Input")
    uploaded = st.file_uploader("CSV or XLSX", type=["csv", "xlsx"])
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Set OPENAI_API_KEY before generating summaries.")
    st.markdown("**Required columns:** `title`, `url`\n\nOptional: `notes`")

if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
else:
    df = pd.read_csv("data/articles.csv")

required = {"title", "url"}
if not required.issubset(df.columns):
    st.error(f"Missing columns: {sorted(required - set(df.columns))}")
    st.stop()

st.subheader("Reading list")
st.dataframe(df, use_container_width=True, hide_index=True)

if st.button("Generate summaries", type="primary", disabled=not bool(os.getenv("OPENAI_API_KEY"))):
    results = []
    progress = st.progress(0)
    for i, row in df.iterrows():
        try:
            text = fetch_article(row["url"])
            summary = summarize(str(row["title"]), str(row["url"]), text, str(row.get("notes", "")))
            results.append({"title": row["title"], "url": row["url"], "summary": summary, "status": "OK"})
        except Exception as e:
            results.append({"title": row["title"], "url": row["url"], "summary": f"ERROR: {e}", "status": "ERROR"})
        progress.progress((i + 1) / len(df))
    st.session_state.results = results

if "results" in st.session_state:
    results = st.session_state.results
    st.subheader("Summaries")
    for r in results:
        with st.expander(f"{r['status']} — {r['title']}", expanded=True):
            st.markdown(r["summary"])
    md = to_markdown(results)
    st.download_button("Download Markdown", md, "research-summaries.md", "text/markdown")
    html = "<html><body><h1>Research Reading Summaries</h1>" + "".join(f"<article><pre style='white-space:pre-wrap'>{r['summary']}</pre></article><hr>" for r in results) + "</body></html>"
    st.download_button("Download shareable HTML", html, "research-summaries.html", "text/html")

st.divider()
st.caption("Privacy note: article text is sent to the configured AI provider only during summarization. Avoid sensitive content unless approved for that provider/account.")
