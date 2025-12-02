TriageFlow: The Executive AI Productivity System 📧 🤖
Course: COT6930 Generative Intelligence and Software Development Lifecycles (Fall 2025)

Instructor: Dr. Fernando Koch

Team: Inbox Nexus

Developer: Hemanth Kumar Sabbavarapu

📋 Executive Summary
TriageFlow is a Multi-Agent Generative Intelligence System designed to solve the critical "Inbox Bottleneck" faced by modern executives.

Executives lose 3–4 hours daily to manual email administration. TriageFlow acts as an Intelligent Outlook Integration, utilizing a 5-Agent Architecture to autonomously filter noise, research historical context (RAG), and draft style-matched replies. Unlike standard AI tools, TriageFlow features Temporal Intelligence, ensuring it can distinguish between "Active" (2025) and "Stale" (2020) corporate policies to prevent hallucinations.

⚡ Key Features
1. 🧠 Multi-Agent Architecture (Microsoft Semantic Kernel)
Instead of a single prompt, we use specialized agents:

Gatekeeper Agent: Classifies email into Spam, FYI, Low, or High Urgency.

Temporal Research Agent: Performs RAG (Retrieval-Augmented Generation) but filters data by recency (e.g., ignoring 2020 travel policies in favor of 2025 rules).

Drafter Agent: Generates responses mimicking the executive's specific tone.

Delegation Agent: Automatically extracts tasks (Who, What, Due Date) for Jira/Asana.

Refiner Agent: A feedback loop agent that rewrites drafts based on user instructions (e.g., "Make it sterner").

2. 📅 Temporal Intelligence Engine
The system includes a "Time Lock" mechanism. It detects conflicting data in the knowledge base and prioritizes the most recent "Active" policy, flagging the decision with a UI badge (📅 2025 DATA LOCK) to ensure compliance safety.

3. 🛡️ Human-in-the-Loop & Safety
Approval Gate: The AI never sends emails autonomously. It presents a proposed draft for review.

Stateful Refinement: Users can iteratively refine drafts using natural language, with the system versioning every change.

🏗️ System Architecture
Code snippet

graph TD
    %% Nodes
    Email[📩 Incoming Email]
    
    subgraph "TriageFlow Brain (Semantic Kernel)"
        Class[🤖 Agent 1: Classifier]
        RAG[📚 Agent 2: Temporal Research]
        Draft[✍️ Agent 3: Drafter]
        Del[👉 Agent 4: Delegator]
        Refine[🧠 Agent 5: Refiner]
    end
    
    subgraph "Knowledge Base"
        DB[(Corp Policies)]
    end

    subgraph "User Interface (Streamlit)"
        SpamUI[🗑️ Spam/Block UI]
        LowUI[💤 Ack/Snooze UI]
        ReviewUI{👤 Human Approval Gate}
        Action[✅ Send Email / Create Ticket]
    end

    %% Flow
    Email --> Class
    Class -- "Spam" --> SpamUI
    Class -- "FYI / Low" --> LowUI
    Class -- "High / Action" --> RAG
    
    RAG -- "Query (Active vs Stale)" --> DB
    DB -- "Active Context (2025)" --> RAG
    
    RAG --> Draft
    RAG --> Del
    
    Draft --> ReviewUI
    Del --> ReviewUI
    
    ReviewUI -- "Refine Request" --> Refine
    Refine -- "New Version" --> ReviewUI
    
    ReviewUI -- "Approve" --> Action
    
    %% Styling
    style Class fill:#0078D4,color:white
    style RAG fill:#0078D4,color:white
    style Draft fill:#0078D4,color:white
    style Del fill:#0078D4,color:white
    style Refine fill:#ff9800,color:white
    style ReviewUI fill:#4caf50,color:white
🚀 Installation & Setup
1. Clone the Repository
Bash

git clone https://github.com/Hemanth15220/TriageFlow_MVP.git
cd TriageFlow_MVP
2. Install Dependencies
This project requires Python 3.9+ and the Microsoft Semantic Kernel SDK.

Bash

pip install streamlit semantic-kernel openai python-dotenv nest_asyncio
3. Configure Environment Variables
Create a file named .env in the root directory and add your Azure OpenAI credentials:

Code snippet

AZURE_OPENAI_ENDPOINT="https://YOUR_RESOURCE_NAME.openai.azure.com/"
AZURE_OPENAI_KEY="YOUR_API_KEY"
AZURE_DEPLOYMENT_NAME="gpt-4o"
4. Run the Application
Start the Streamlit interface:

Bash

streamlit run app.py
🎮 How to Demo (Walkthrough)
Scenario 1: Temporal Intelligence (The "Time Lock")

Select the email "Travel Request: NY to LA" (High Priority).

Click 🚀 Analyze Email.

Observe the "📅 2025 DATA LOCK" badge in the sidebar.

Explanation: The AI found two policies (2020 vs 2025) and correctly used the 2025 Business Class rule to approve the request, ignoring the stale data.

Scenario 2: The Refinement Loop

Look at the generated draft.

Click ✏️ Refine and type: "Make it more casual and shorter."

Click Update Draft.

Explanation: The Refiner Agent rewrites the text in real-time, demonstrating the stateful feedback loop.

Scenario 3: Delegation

Select the "Task: Update Board Deck" email.

Click the 👉 Delegate tab.

Explanation: The system automatically extracted the Task ("Update slides"), the Owner ("Me"), and the Deadline ("Friday").

📂 File Structure
app.py: The main entry point containing the Streamlit UI and Semantic Kernel Agent Logic.

mock_data.py: A procedural generator that creates realistic email scenarios (Spam, Crisis, Approvals) and contains the "Knowledge Base" with conflicting dates.

.env: (Not included in repo) Stores API keys.

⚖️ License
This project is licensed under the MIT License - see the LICENSE file for details.
