import streamlit as st
import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from mock_data import generate_mock_emails, knowledge_base

# --- 0. CRITICAL FIX FOR ASYNC LOOPS ---
nest_asyncio.apply()

# --- 1. CONFIG & SETUP ---
st.set_page_config(layout="wide", page_title="Outlook | TriageFlow", page_icon="📧")
load_dotenv()

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; font-family: 'Segoe UI', sans-serif; }
    .outlook-header { background-color: #0078D4; color: white; padding: 12px 20px; font-weight: 600; font-size: 16px; }
    .email-item { padding: 10px; border-bottom: 1px solid #e1dfdd; background: white; cursor: pointer; }
    .reading-pane { background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); min-height: 500px; }
    .temporal-badge { background-color: #dff6dd; color: #107c10; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #107c10; }
    
    /* Success Card Styling */
    .success-card { background-color: #dff6dd; padding: 30px; border-radius: 8px; border: 1px solid #107c10; text-align: center; margin-top: 20px;}
    .success-text { color: #107c10; font-weight: 700; font-size: 18px; margin-bottom: 10px; }
    .success-detail { color: #333; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- 3. SEMANTIC KERNEL SETUP ---
@st.cache_resource
def setup_kernel():
    kernel = sk.Kernel()
    kernel.add_service(
        AzureChatCompletion(
            service_id="default",
            deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY")
        )
    )
    
    # 1. CLASSIFIER
    kernel.add_function(
        prompt="""Analyze email. Subject: {{$subject}} Body: {{$body}}. 
        Rules:
        - Sales/Marketing -> 'Spam'
        - Informational/No Task -> 'FYI'
        - Casual/No Deadline -> 'Low'
        - Deadline/Crisis/Approval -> 'High'
        Return ONLY: "Urgency: [High/Low] | Intent: [Action/FYI/Spam]" """,
        function_name="ClassifyEmail", plugin_name="TriagePlugin"
    )

    # 2. DRAFTER
    kernel.add_function(
        prompt="Exec Asst. Email: {{$body}} Context: {{$context}} Draft reply in STYLE: {{$style}}.",
        function_name="DraftReply", plugin_name="TriagePlugin"
    )
    
    # 3. REFINER
    kernel.add_function(
        prompt="Rewrite this draft based on feedback. \nOriginal: {{$previous_draft}}\nFeedback: {{$feedback}}\nNew Draft:",
        function_name="RefineDraft", plugin_name="TriagePlugin"
    )
    
    # 4. DELEGATOR
    kernel.add_function(
        prompt="Extract task: {{$body}}. Format: 'Task: [Action] | Who: [Role] | Due: [Time]'",
        function_name="ExtractTask", plugin_name="TriagePlugin"
    )
    return kernel

kernel = setup_kernel()

# --- 4. ASYNC HELPER ---
def run_async(coroutine):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

# --- 5. LOGIC PIPELINE ---
def agent_pipeline(email_obj, current_style):
    # 1. Classify
    classify_func = kernel.plugins["TriagePlugin"]["ClassifyEmail"]
    cls_str = str(run_async(kernel.invoke(classify_func, KernelArguments(subject=email_obj["subject"], body=email_obj["body"]))))

    # 2. Context (RAG)
    hits = []
    temporal_lock = False
    for k, v in knowledge_base.items():
        if k.split("(")[0].strip() in email_obj["body"]:
            if "OLD POLICY" in v: continue 
            if "ACTIVE" in v or "2025" in k:
                hits.append(f"✅ {k}: {v}")
                temporal_lock = True
            else:
                hits.append(f"🔹 {k}: {v}")
    context_str = "\n".join(hits) if hits else "ℹ️ No specific policy found."
    
    # 3. Logic Branching
    draft_str = ""
    delegate_str = ""
    
    if "Spam" not in cls_str:
        draft_func = kernel.plugins["TriagePlugin"]["DraftReply"]
        draft_str = str(run_async(kernel.invoke(draft_func, KernelArguments(body=email_obj["body"], context=context_str, style=current_style))))
    
    if "High" in cls_str or "Action" in cls_str:
        del_func = kernel.plugins["TriagePlugin"]["ExtractTask"]
        delegate_str = str(run_async(kernel.invoke(del_func, KernelArguments(body=email_obj["body"]))))

    return {
        "class": cls_str, 
        "context": context_str, 
        "draft": draft_str, 
        "delegate": delegate_str, 
        "temporal_lock": temporal_lock,
        "status": "active",
        "resolution_msg": "",
        "version": 0 # <--- NEW: Tracks Draft Versions
    }

def refine_draft_logic(previous_draft, user_feedback):
    func = kernel.plugins["TriagePlugin"]["RefineDraft"]
    return str(run_async(kernel.invoke(func, KernelArguments(previous_draft=previous_draft, feedback=user_feedback))))

# --- 6. STATE HELPERS ---
def mark_done(eid, message):
    st.session_state.analysis_cache[eid]['status'] = 'completed'
    st.session_state.analysis_cache[eid]['resolution_msg'] = message
    st.rerun()

def undo_action(eid):
    st.session_state.analysis_cache[eid]['status'] = 'active'
    st.rerun()

# --- 7. INITIALIZATION ---
if "emails" not in st.session_state: st.session_state.emails = generate_mock_emails(15)
if "selected_id" not in st.session_state: st.session_state.selected_id = st.session_state.emails[0]['id']
if "analysis_cache" not in st.session_state: st.session_state.analysis_cache = {}
if "user_style" not in st.session_state: st.session_state.user_style = knowledge_base['Executive Tone']

# --- 8. UI LAYOUT ---
st.markdown('<div class="outlook-header">🟦 Outlook &nbsp;&nbsp; 🔍 Search</div>', unsafe_allow_html=True)
c_folders, c_list, c_read, c_ai = st.columns([1, 2.5, 4.5, 3])

# 1. Folders
with c_folders:
    st.markdown("### Folders")
    st.button("📥 Inbox", use_container_width=True)
    st.button("📤 Sent", use_container_width=True)
    st.button("🗑️ Trash", use_container_width=True)

# 2. List
with c_list:
    st.text_input("Search", label_visibility="collapsed")
    st.write("") 
    for email in st.session_state.emails:
        is_done = False
        if email['id'] in st.session_state.analysis_cache:
            if st.session_state.analysis_cache[email['id']].get('status') == 'completed':
                is_done = True

        border = "2px solid #0078D4" if email['id'] == st.session_state.selected_id else "1px solid #eee"
        with st.container(border=True):
            label = f"**{email['sender']}**\n\n{email['subject']}"
            if is_done: label = "✅ " + label
            
            if st.button(label, key=email['id'], use_container_width=True):
                st.session_state.selected_id = email['id']
                st.rerun()

# 3. Reading Pane
current = next((e for e in st.session_state.emails if e['id'] == st.session_state.selected_id), None)
with c_read:
    if current:
        with st.container():
            st.markdown(f"## {current['subject']}")
            st.caption(f"**From:** {current['sender']} | **Received:** {current['received']}")
            st.divider()
            st.markdown(f"""<div class="reading-pane">{current['body'].replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)

# 4. AI SIDEBAR
with c_ai:
    st.subheader("⚡ TriageFlow Agent")
    
    if current:
        eid = current['id']
        data = st.session_state.analysis_cache.get(eid)
        
        with st.container(border=True):
            if not data:
                st.info("Agent Standing By")
                if st.button("🚀 Analyze Email", type="primary", use_container_width=True):
                    with st.spinner("Classifying..."):
                        res = agent_pipeline(current, st.session_state.user_style)
                        st.session_state.analysis_cache[eid] = res
                        st.rerun()
            
            # --- VIEW: COMPLETED ---
            elif data.get('status') == 'completed':
                st.markdown(f"""
                <div class="success-card">
                    <h1>✅</h1>
                    <div class="success-text">Action Completed</div>
                    <div class="success-detail">{data['resolution_msg']}</div>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("↩️ Undo", key=f"undo_{eid}", use_container_width=True):
                    undo_action(eid)

            # --- VIEW: ACTIVE WORKFLOW ---
            else:
                # Header Badge
                header_color = "#gray"
                if "High" in data['class']: header_color = "#d32f2f" 
                elif "FYI" in data['class']: header_color = "#f57c00" 
                elif "Spam" in data['class']: header_color = "#000000" 
                else: header_color = "#388e3c" 
                
                st.markdown(f"""
                <div style="background-color:{header_color}; color:white; padding:8px; border-radius:5px; margin-bottom:10px;">
                    {data['class']}
                </div>
                """, unsafe_allow_html=True)
                
                # --- SCENARIO 1: SPAM ---
                if "Spam" in data['class']:
                    st.warning("⚠️ High confidence this is spam.")
                    c1, c2 = st.columns(2)
                    with c1: 
                        if st.button("🗑️ Delete", use_container_width=True):
                            mark_done(eid, "Email moved to Trash.")
                    with c2: 
                        if st.button("🚫 Block", use_container_width=True):
                            mark_done(eid, "Sender blocked and email deleted.")
                
                # --- SCENARIO 2: FYI / LOW ---
                elif "FYI" in data['class'] or "Low" in data['class']:
                    st.info("ℹ️ Information only.")
                    c1, c2 = st.columns(2)
                    with c1: 
                        if st.button("👍 Ack", use_container_width=True):
                            mark_done(eid, f"Quick acknowledgment sent to {current['sender']}")
                    with c2: 
                        if st.button("💤 Snooze", use_container_width=True):
                            mark_done(eid, "Snoozed for 4 hours.")

                # --- SCENARIO 3: HIGH / ACTION ---
                else:
                    with st.expander("📚 Knowledge Retrieval", expanded=True):
                        if data['temporal_lock']:
                            st.markdown('<div class="temporal-badge">📅 2025 DATA LOCK</div>', unsafe_allow_html=True)
                        st.markdown(data['context'])

                    tab1, tab2 = st.tabs(["📝 Draft Reply", "👉 Delegate"])
                    
                    with tab1:
                        # --- THE REFINE FIX: VERSIONED KEYS ---
                        # We use a version number in the key. When version increments,
                        # Streamlit throws away the old text box and renders a new one with the new text.
                        current_version = data.get('version', 0)
                        
                        # The text box always displays whatever is in 'draft'
                        draft_val = st.text_area("AI Draft:", value=data['draft'], height=200, key=f"draft_box_{eid}_v{current_version}")
                        
                        c1, c2 = st.columns(2)
                        with c1: 
                            if st.button("✅ Send", key=f"s_{eid}", use_container_width=True):
                                mark_done(eid, f"Reply sent to {current['sender']}")
                        with c2:
                            with st.popover("Refine"):
                                fb = st.text_input("Instructions:", key=f"fb_{eid}")
                                if st.button("Update Draft", key=f"up_{eid}"):
                                    with st.spinner("Rewriting..."):
                                        # 1. Generate new text
                                        new_d = refine_draft_logic(draft_val, fb)
                                        # 2. Update Cache
                                        st.session_state.analysis_cache[eid]['draft'] = new_d
                                        # 3. Increment Version (This forces the UI to refresh)
                                        st.session_state.analysis_cache[eid]['version'] = current_version + 1
                                        st.rerun()

                    with tab2:
                        if data.get('delegate') and len(data['delegate']) > 10:
                            st.success("Task Identified")
                            st.text_area("Details", value=data['delegate'], height=100)
                            if st.button("Create Jira Ticket", use_container_width=True):
                                mark_done(eid, "Jira Ticket #PROJ-402 created successfully.")
                        else:
                            st.info("No tasks identified.")
