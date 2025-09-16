

import streamlit as st
import pandas as pd
import pdfplumber


# ------------------------------
# Call Ollama CLI with context + question
# ------------------------------
import requests
import json

def answer_question(context, question):
    prompt = f"""You are a financial analyst.
Context:
{context}

Question: {question}
Answer in simple words:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama2", "prompt": prompt, "stream": False}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "⚠️ No answer received")
        else:
            return f"⚠️ API Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"⚠️ Error calling Ollama API: {e}"


# ------------------------------
# Convert dataframe → plain text context
# ------------------------------
def create_context_from_df(df):
    context = ""
    for col in df.columns:
        values = df[col].dropna().astype(str).tolist()
        for val in values:
            context += f"{col}: {val}\n"
    return context[:3000]  # limit context length to avoid overload

# ------------------------------
# PDF Extraction
# ------------------------------
def extract_pdf_data(pdf_file):
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                data.append(df)
            else:
                text = page.extract_text()
                if text:
                    df = pd.DataFrame({"Content": text.split("\n")})
                    data.append(df)
    if data:
        return pd.concat(data, ignore_index=True)
    else:
        return pd.DataFrame()

# ------------------------------
# Excel Extraction
# ------------------------------
def extract_excel_data(excel_file):
    xls = pd.ExcelFile(excel_file)
    df_list = [xls.parse(sheet) for sheet in xls.sheet_names]
    return pd.concat(df_list, ignore_index=True)

# ------------------------------
# Streamlit App
# ------------------------------
st.set_page_config(page_title="Financial Q&A Assistant", layout="wide")
st.title("📊 Financial Document Q&A Assistant")

uploaded_file = st.file_uploader("Upload PDF or Excel", type=["pdf", "xlsx", "xls"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        df = extract_pdf_data(uploaded_file)
    else:
        df = extract_excel_data(uploaded_file)

    if not df.empty:
        st.subheader("📄 Extracted Data Preview")
        st.dataframe(df.head(15))

        # build context
        context = create_context_from_df(df)

        question = st.text_input("💬 Ask a question about this financial document:")

        if question:
            with st.spinner("Thinking..."):
                answer = answer_question(context, question)
                st.success("✅ Answer")
                st.write(answer)

    else:
        st.warning("⚠️ No data extracted. Try another document or check format.")

