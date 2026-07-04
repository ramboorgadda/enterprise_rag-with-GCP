import os
import json
from typing import Any
from urllib import error, request

import streamlit as st


st.set_page_config(page_title="Enterprise RAG Evals", page_icon="🧪", layout="wide")

backend_url = os.getenv("BACKEND_URL", "").strip()
judge_model = os.getenv("JUDGE_GROQ", "llama-3.3-70b-versatile").strip()

st.title("Enterprise RAG Evals")
st.caption("Lightweight eval runner deployed as a dedicated Cloud Run service.")

left, right = st.columns(2)
left.metric("Judge Model", judge_model)
right.metric("Backend Configured", "Yes" if backend_url else "No")

st.divider()
st.subheader("Smoke Test")
question = st.text_input("Question", value="What is this system designed to do?")

if st.button("Run Backend Query", type="primary"):
    if not backend_url:
        st.error("BACKEND_URL is not set.")
    else:
        endpoint = backend_url.rstrip("/") + "/query"
        payload: dict[str, Any] = {"query": question, "thread_id": "evals-smoke-test"}

        with st.spinner("Calling backend..."):
            try:
                req = request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with request.urlopen(req, timeout=60) as response:
                    raw = response.read().decode("utf-8")
                data = json.loads(raw)

                st.success("Query succeeded")
                st.write("Status:", data.get("status"))
                st.write("Answer:")
                st.write(data.get("answer", ""))

                thought_process = data.get("thought_process") or []
                if thought_process:
                    st.write("Thought Process:")
                    for item in thought_process:
                        st.write(f"- {item}")
            except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
                st.error(f"Backend call failed: {exc}")

st.divider()
st.subheader("Health")
st.code(
    f"BACKEND_URL={backend_url or 'unset'}\n"
    f"JUDGE_GROQ={judge_model or 'unset'}",
    language="bash",
)
