print("DEBUG: The script is starting...")

import asyncio
import os
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
# FIX: Import KernelArguments directly
from semantic_kernel.functions import KernelArguments
from mock_data import incoming_emails, knowledge_base

# --- SETUP ---
load_dotenv()
kernel = sk.Kernel()

# Configure Azure AI Service
deployment_name = "gpt-4o" 
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_KEY")

# Add Azure Service to Kernel
kernel.add_service(
    AzureChatCompletion(
        service_id="default",
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key
    )
)

# --- AGENT 1: CLASSIFICATION ---
classify_prompt = """
Analyze the following email.
Subject: {{$subject}}
Body: {{$body}}

Return ONLY a concise classification string in this format: 
"Urgency: [High/Medium/Low] | Intent: [Task/Question/FYI]"
"""
classify_func = kernel.add_function(
    prompt=classify_prompt,
    function_name="ClassifyEmail",
    plugin_name="TriagePlugin"
)

# --- AGENT 2: RESEARCH (RAG) ---
def research_logic(email_body):
    print("   🔍 [Research Agent]: Scanning Knowledge Base...")
    context_found = []
    for topic, info in knowledge_base.items():
        if topic in email_body:
            context_found.append(f"FACT: {info}")
    
    context_found.append(f"STYLE: {knowledge_base['Executive Tone']}")
    return "\n".join(context_found)

# --- AGENT 3: DRAFTER ---
draft_prompt = """
You are an executive assistant.
Incoming Email: {{$body}}

Use this Context to answer: 
{{$context}}

Draft a reply. Follow the STYLE guide strictly.
Draft:
"""
draft_func = kernel.add_function(
    prompt=draft_prompt,
    function_name="DraftReply",
    plugin_name="TriagePlugin"
)

# --- MAIN EXECUTION ---
async def main():
    print("\n--- 🚀 STARTING TRIAGEFLOW (GPT-4o) ---\n")

    for email in incoming_emails:
        print(f"📩 NEW EMAIL: {email['subject']}")
        
        # 1. CLASSIFY
        # FIX: Use KernelArguments() instead of sk.KernelArguments()
        classification = await kernel.invoke(
            classify_func, 
            KernelArguments(subject=email["subject"], body=email["body"])
        )
        print(f"   🤖 [Classification]: {classification}")

        if "High" in str(classification) or "Question" in str(classification):
            # 2. RESEARCH
            context_data = research_logic(email["body"])
            print(f"   📚 [Context Found]: {context_data}")

            # 3. DRAFT
            draft = await kernel.invoke(
                draft_func,
                KernelArguments(body=email["body"], context=context_data)
            )
            
            # 4. APPROVAL GATE
            print(f"\n📝 [AI DRAFT PROPOSAL]:\n{'-'*30}\n{draft}\n{'-'*30}")
            user_choice = input("👤 [HUMAN GATE] Approve this draft? (y/n): ")
            
            if user_choice.lower() == 'y':
                print("✅ EMAIL SENT.\n")
            else:
                print("❌ DRAFT DISCARDED.\n")
        else:
            print("   💤 Low priority. Archived.\n")

if __name__ == "__main__":
    asyncio.run(main())