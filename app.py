import streamlit as st
import asyncio
import os
import time
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from mock_data import generate_mock_emails, knowledge_base

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="TriageFlow | Auto-Pilot", page_icon="🛡️", layout="wide")
load_dotenv()

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; color: #212529; }
    
    /* Status Cards */
    .stat-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }
    .stat-num { font-size: 24px; font-weight: bold; color: #0D6EFD; }
    .stat-label { font-size: 12px; color: #6C757D; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Email Card */
    .action-card { 
        background-color: white; 
        padding: 30px; 
        border-radius: 15px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        border-left: 8px solid #0D6EFD; /* Blue accent for focus */
    }
    
    /* AI Badge */
    .ai-badge { 
        background-color: #E8F0FE; 
        color: #0D6EFD; 
        padding: 4px 12px; 
        border-radius: 20px; 
        font-weight: 600; 
        font-size: 12px; 
        display: inline-block;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. STATE MANAGEMENT ---
if "emails" not in st.session_state:
    st.session_state.emails = generate_mock_emails(300)
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "stats" not in st.session_state:
    st.session_state.stats = {"spam_blocked": 0, "fyi_filed": 0, "actions_taken": 0}
if "processing" not in st.session_state:
    st.session_state.processing = False

# --- 3. AI KERNEL ---
@st.cache_resource
def setup_kernel():
    kernel = sk.Kernel()
    deployment = "gpt-4o" 
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_KEY")
    
    # Fallback for UI demo if keys missing
    if not key: return None 

    kernel.add_service(
        AzureChatCompletion(service_id="default", deployment_name=deployment, endpoint=endpoint, api_key=key)
    )
    return kernel

kernel = setup_kernel()

# --- 4. AGENT LOGIC ---
async def agent_classify(subject, body):
    # For speed in demo, we can use a faster prompt or simulated logic if needed
    # But here is the real AI call:
    prompt = """
    Classify email. Return ONLY one word: [Spam, FYI, Important, Actionable].
    Email: {{$subject}} - {{$body}}
    """
    if not kernel: return "Actionable" # Fallback
    
    func = kernel.add_function(prompt=prompt, function_name="Classify", plugin_name="Triage")
    return await kernel.invoke(func, KernelArguments(subject=subject, body=body))

def agent_research(body):
    hits = []
    for key, val in knowledge_base.items():
        if key.lower() in body.lower():
            hits.append(f"🔹 {val}")
    if not hits: hits.append("No specific policy found. Relying on standard executive judgment.")
    return "\n".join(hits)

async def agent_draft(body, context):
    prompt = """
    You are an Executive Chief of Staff. 
    Context: {{$context}}
    Email: {{$body}}
    Task: Draft a concise, decisive reply. Use the context. 
    """
    func = kernel.add_function(prompt=prompt, function_name="Draft", plugin_name="Triage")
    return await kernel.invoke(func, KernelArguments(body=body, context=context))

# --- 5. AUTO-PILOT LOGIC (The "Gatekeeper") ---
async def process_until_actionable():
    """Loops through emails, auto-archiving junk, stopping ONLY for action."""
    
    container = st.empty() # For showing "Scanning..." UI
    
    while st.session_state.current_index < len(st.session_state.emails):
        idx = st.session_state.current_index
        email = st.session_state.emails[idx]
        
        # Show scanning progress
        container.info(f"Scanning Email #{idx+1}: {email['subject']}...")
        
        # 1. Classify
        category_result = await agent_classify(email['subject'], email['body'])
        category = str(category_result).strip().replace(".", "")
        
        # 2. Decision Logic
        if "Spam" in category:
            st.session_state.stats["spam_blocked"] += 1
            st.session_state.current_index += 1
            # Loop continues immediately (Auto-Archive)
            
        elif "FYI" in category:
            st.session_state.stats["fyi_filed"] += 1
            st.session_state.current_index += 1
            # Loop continues immediately (Auto-File)
            
        else:
            # It is "Important" or "Actionable" -> STOP LOOP
            container.empty() # Clear scanning message
            return category # Return control to UI for Human Review
            
    return "Done"

# --- 6. UI LAYOUT ---

# Header Stats
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{len(st.session_state.emails) - st.session_state.current_index}</div><div class="stat-label">Pending Scan</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{st.session_state.stats["spam_blocked"]}</div><div class="stat-label">Spam Blocked</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{st.session_state.stats["fyi_filed"]}</div><div class="stat-label">FYI Filed</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{st.session_state.stats["actions_taken"]}</div><div class="stat-label">Actions Taken</div></div>', unsafe_allow_html=True)

st.write("---")

# Main Action Area
if st.session_state.current_index < len(st.session_state.emails):
    
    # If we haven't analyzed the current email yet, run the Auto-Pilot loop
    if not st.session_state.get("ready_for_review"):
        
        # Start Button to trigger the "Work"
        if st.button("🛡️ Start Triage Auto-Pilot", type="primary"):
            category = asyncio.run(process_until_actionable())
            
            if category == "Done":
                st.success("Inbox Zero!")
                st.stop()
            
            # If we are here, we hit an Actionable email
            idx = st.session_state.current_index
            email = st.session_state.emails[idx]
            
            # Pre-calculate context and draft for the User View
            context = agent_research(email['body'])
            draft = asyncio.run(agent_draft(email['body'], context))
            
            # Save state so UI renders
            st.session_state.review_data = {
                "category": category,
                "context": context,
                "draft": str(draft)
            }
            st.session_state.ready_for_review = True
            st.rerun()
            
        else:
            st.info("Click start to let the agents scan your inbox. They will only stop for important items.")

    # --- HUMAN REVIEW INTERFACE ---
    # We only show this if the Auto-Pilot found something worth your time
    else:
        idx = st.session_state.current_index
        email = st.session_state.emails[idx]
        data = st.session_state.review_data
        
        st.markdown(f"### 🚨 Review Required: {data['category'].upper()}")
        
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.markdown(f"""
            <div class="action-card">
                <div style="color:#666; font-size:12px; margin-bottom:5px;">FROM: {email['sender']}</div>
                <h3 style="margin-top:0;">{email['subject']}</h3>
                <p>{email['body']}</p>
                <hr>
                <small><b>🧠 AI Context (RAG):</b><br>{data['context']}</small>
            </div>
            """, unsafe_allow_html=True)
            
        with c_right:
            st.markdown('<div class="ai-badge">✨ AI SUGGESTED ACTION</div>', unsafe_allow_html=True)
            
            edited_draft = st.text_area("Proposed Reply:", value=data['draft'], height=200)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Approve & Send", type="primary", use_container_width=True):
                    st.toast("Action Taken!", icon="🚀")
                    st.session_state.stats["actions_taken"] += 1
                    st.session_state.current_index += 1
                    st.session_state.ready_for_review = False # Reset loop
                    st.rerun()
            
            with col_b:
                if st.button("⏩ Skip / Archive", use_container_width=True):
                    st.session_state.current_index += 1
                    st.session_state.ready_for_review = False # Reset loop
                    st.rerun()

else:
    st.balloons()
    st.markdown("<h1 style='text-align: center;'>🎉 Inbox Zero Achieved</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>The agents have filtered all noise and processed all actions.</p>", unsafe_allow_html=True)
    if st.button("Reset Simulation"):
        st.session_state.clear()
        st.rerun()