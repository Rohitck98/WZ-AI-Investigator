from pathlib import Path
import streamlit as st
from src.data_loader import load_workzones
from src.query_engine import answer_question

st.set_page_config(page_title="Work Zone Investigator", page_icon="🚧", layout="wide")
st.title("🚧 Work Zone Investigator")
st.caption("Explore and investigate work zone data using natural-language questions.")

with st.sidebar:
    st.header("Data")
    upload=st.file_uploader("Upload a work-zone CSV", type=["csv"])
    default=Path("data/Sample 1.csv")
    source=upload if upload is not None else (default if default.exists() else None)
    if st.button("Clear chat"):
        st.session_state.messages=[]
        st.rerun()

if source is None:
    st.info("Upload your CSV in the sidebar, or save it as data/Sample 1.csv.")
    st.stop()

try:
    df,schema=load_workzones(source)
except Exception as exc:
    st.error(f"Could not read the CSV: {exc}")
    st.stop()

with st.sidebar:
    st.success(f"Loaded {len(df):,} rows")

with st.expander("Preview cleaned data"):
    st.dataframe(df.head(100), use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages=[]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("filters"): st.caption("Applied: " + " | ".join(message["filters"]))
        if message.get("data") is not None: st.dataframe(message["data"], use_container_width=True)

question=st.chat_input("Ask about roads, directions, dates, closures, counts, or keywords")
if question:
    st.session_state.messages.append({"role":"user","content":question})
    with st.chat_message("user"): st.markdown(question)
    answer,result,filters=answer_question(df,schema,question)
    shown=result.head(200)
    with st.chat_message("assistant"):
        st.markdown(answer)
        st.caption("Applied: " + " | ".join(filters))
        st.dataframe(shown, use_container_width=True)
        st.download_button("Download matching records", result.to_csv(index=False).encode("utf-8"), "workzone_results.csv", "text/csv")
    st.session_state.messages.append({"role":"assistant","content":answer,"filters":filters,"data":shown})
