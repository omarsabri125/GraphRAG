import streamlit as st
import requests
import time

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="GraphFlow AI", 
    page_icon="🕸️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Custom Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    
    .stChatMessage {
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #30363d;
    }
    
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #58a6ff;
    }

    /* Style for the mode buttons to look like a unified switch */
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #21262d;
        color: white;
        border: 1px solid #30363d;
    }
    
    div.stButton > button:hover {
        border-color: #58a6ff;
        color: #58a6ff;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph_context" not in st.session_state:
    st.session_state.graph_context = []
if "last_latency" not in st.session_state:
    st.session_state.last_latency = "0ms"
# Default mode
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "Search"

# --- 4. Metric Render Function ---
def display_metrics(container):
    with container.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Messages", len(st.session_state.messages))
        m2.metric("User Queries", len([m for m in st.session_state.messages if m["role"] == "user"]))
        m3.metric("Graph Hits", len(st.session_state.graph_context))
        m4.metric("Latency", st.session_state.last_latency)

# --- 5. Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
    st.title("GraphFlow AI")
    st.caption("Advanced Knowledge Graph RAG")
    st.divider()
    st.subheader("⚙️ Engine Settings")
    top_k = st.slider("Top K Nodes", 1, 20, 7)
    
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.session_state.graph_context = []
        st.session_state.last_latency = "0ms"
        st.rerun()
    st.info("**Backend Status:** Online", icon="✅")

# --- 6. Header & Top Metrics ---
st.title("🤖 Knowledge Graph Assistant")
metric_holder = st.empty()
display_metrics(metric_holder)
st.divider()

# --- 7. NEW: Button-Based Mode Selection ---
st.markdown(f"**Current Intelligence Mode:** `{st.session_state.active_mode}`")
btn_col1, btn_col2, btn_spacer = st.columns([1, 1, 2])

with btn_col1:
    # If this is the active mode, we use primary styling
    search_type = "primary" if st.session_state.active_mode == "Search" else "secondary"
    if st.button("🔍 Search Only", type=search_type, use_container_width=True):
        st.session_state.active_mode = "Search"
        st.rerun()

with btn_col2:
    answer_type = "primary" if st.session_state.active_mode == "Answer" else "secondary"
    if st.button("🧠 Generate Answer", type=answer_type, use_container_width=True):
        st.session_state.active_mode = "Answer"
        st.rerun()

st.write("") # Spacer

# --- 8. Chat History Display ---
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if "results" in message:
            with st.expander("View Source Nodes"):
                for idx, r in enumerate(message["results"], 1):
                    st.caption(f"Node {idx} | Score: {r.get('score', 0):.4f}")
                    st.write(r.get('text', 'No content'))

# --- 9. Input Logic & Backend Processing ---
if prompt := st.chat_input(f"Mode: {st.session_state.active_mode} | Type your query here..."):
    start_time = time.time()
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.status(f"Running {st.session_state.active_mode}...", expanded=True) as status:
            try:
                # Logic based on st.session_state.active_mode
                if st.session_state.active_mode == "Search":
                    payload = {"text": prompt, "limit": top_k}
                    response = requests.post("http://fastapi:8001/api/v1/index/search", json=payload, timeout=30)
                    results = response.json().get("results", [])
                    st.session_state.graph_context = results
                    
                    status.update(label="Search complete!", state="complete", expanded=False)
                    ans_text = f"Retrieved **{len(results)}** nodes from the graph."
                    st.markdown(ans_text)
                    for idx, r in enumerate(results, 1):
                        with st.expander(f"Node {idx}: Score {r.get('score', 0):.3f}"):
                            st.write(r.get('text'))
                    st.session_state.messages.append({"role": "assistant", "content": ans_text, "results": results})

                else: # Answer Mode
                    payload = {"text": prompt, "limit": top_k}
                    response = requests.post("http://fastapi:8001/api/v1/index/answer", json=payload, timeout=60)
                    result = response.json()
                    
                    is_cached = result.get("signal") == "cache_answer_success"
                    answer = result.get("answer_from_cache" if is_cached else "answer", "No answer found")
                    
                    status.update(label="Answer Ready!", state="complete", expanded=False)
                    if is_cached: st.caption("⚡ *Retrieved from Cache*")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                # Post-Process: Update metrics
                st.session_state.last_latency = f"{int((time.time() - start_time) * 1000)}ms"
                display_metrics(metric_holder)

            except Exception as e:
                status.update(label="Error", state="error")
                st.error(f"Backend Offline: {e}")