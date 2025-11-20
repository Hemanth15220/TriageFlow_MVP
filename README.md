⚡ TriageFlow: The Executive AI Productivity System

Multi-Agent Generative Intelligence for Automated Email Triage

TriageFlow is an autonomous "Chief of Staff" agent designed to solve the executive inbox bottleneck. It uses a Multi-Agent System (MAS) to filter noise, research context, and draft replies, reclaiming 3+ hours of productivity daily.

🚀 Project Overview

This repository contains the MVP v0.1 prototype for the TriageFlow system. It demonstrates a Sequential Multi-Agent Architecture orchestrated by Microsoft Semantic Kernel.

🤖 The Agents

The system is composed of three specialized AI agents working in sequence:

🛡️ Classification Agent (The Gatekeeper):

Role: Analyzes email intent and urgency (High/Medium/Low).

Logic: Filters out "Spam" and "FYI" emails automatically. Only "Actionable" items proceed.

📚 Context Research Agent (The Librarian):

Role: Performs Retrieval-Augmented Generation (RAG).

Logic: Queries a mock corporate knowledge base to find relevant facts, policies, and history associated with the incoming email.

✍️ Response Drafter Agent (The Ghostwriter):

Role: Generates professional replies.

Logic: Uses Few-Shot Prompting to emulate the executive's specific tone and brevity, using the context provided by the Research Agent.

🛠️ Architecture

The system follows a Human-in-the-Loop design pattern for safety.

graph LR
    A[Email Input] --> B[Agent 1: Classification]
    B --> C{Is Urgent?}
    C -- No --> D[Auto-Archive]
    C -- Yes --> E[Agent 2: Context Research]
    E --> F[Agent 3: Response Drafter]
    F --> G[🛑 Human Approval Gate]
    G --> H[Send / Edit / Reject]


💻 Installation & Setup

1. Prerequisites

Python 3.8 or higher

An Azure OpenAI Endpoint & Key (or OpenAI API Key)

2. Clone the Repository

git clone [https://github.com/YOUR_USERNAME/TriageFlow_MVP.git](https://github.com/YOUR_USERNAME/TriageFlow_MVP.git)
cd TriageFlow_MVP


3. Install Dependencies

It is recommended to use a virtual environment.

# Create virtual env (Mac/Linux)
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install streamlit semantic-kernel openai python-dotenv


4. Configure Environment

Create a file named .env in the root folder and add your credentials:

# .env
AZURE_OPENAI_KEY="your_key_here"
AZURE_OPENAI_ENDPOINT="your_endpoint_here"


(Note: The code is configured for gpt-4o by default. You can change this in app.py if needed.)

🏃‍♂️ How to Run the Demo

This prototype includes a Streamlit Web Dashboard to visualize the agent workflow.

Run the application:

streamlit run app.py
