import random
from datetime import datetime, timedelta

# 1. The Knowledge Graph (RAG Source)
knowledge_base = {
    "Project Alpha": "STATUS: CRITICAL. Server migration failed. Rollback in progress. ETA 2:00 PM.",
    "Software Licenses": "POLICY: Expenses >$20k require CFO approval. Forward to finance@company.com.",
    "Merger": "POLICY: STRICT NO COMMENT. Forward inquiries to VP of Comms.",
    "Executive Tone": "Professional, decisive, and brief. No fluff. Sign off with 'Best, [Your Name]'.",
    "Q3 Budget": "DATA: Q3 Marketing Budget remaining is $15,000. Travel budget is depleted.",
    "Hiring Freeze": "POLICY: No new FTE hires until Q1. Contractors are allowed for critical projects."
}

# 2. Templates for Procedural Generation
templates = {
    "Spam": [
        ("Flash Sale!", "Buy one get one free on all office supplies."),
        ("Webinar Invite", "Join us for 'AI in 2025'."),
        ("LinkedIn Notification", "You appeared in 5 searches this week."),
        ("Cold Outreach", "Can we schedule 15 mins to discuss synergy?")
    ],
    "FYI": [
        ("Weekly Digest", "Here are the metrics for the week. No action needed."),
        ("Friday Potluck", "Reminder: Potluck is at 4pm."),
        ("System Maintenance", "IT will be patching servers on Sunday."),
        ("OOO Auto-reply", "I am out of office until Monday.")
    ],
    "Important": [
        ("Q3 Budget Report", "Attached is the final Q3 breakdown. Please review before the board meeting."),
        ("Client Sentiment Analysis", "Recent feedback suggests Nulab account satisfaction is dropping."),
        ("Competitor Alert", "Competitor X just launched a feature similar to our roadmap."),
        ("Security Patch Notice", "Critical vulnerability found in library X. Patch applied.")
    ],
    "Actionable": [
        ("Approval Needed: New Hire", "Can we proceed with the offer for the Senior Dev? (Ref: Hiring Freeze)"),
        ("Urgent: Project Alpha Update?", "Clients are asking about the downtime. What do I tell them?"),
        ("Budget Question", "Can I book a flight to the conf? It's $1,200. (Ref: Q3 Budget)"),
        ("Press Inquiry: Merger", "Reporter asking for comment on the acquisition rumors. Advice?")
    ]
}

def generate_mock_emails(count=300):
    """Generates a weighted list of emails simulating an inbox."""
    emails = []
    
    # Distribution: 20% Spam, 30% FYI, 20% Important, 30% Actionable
    weights = [0.2, 0.3, 0.2, 0.3]
    categories = ["Spam", "FYI", "Important", "Actionable"]
    
    # Generate
    chosen_categories = random.choices(categories, weights=weights, k=count)
    
    for i, category in enumerate(chosen_categories):
        template = random.choice(templates[category])
        subject_prefix = ""
        
        # Simulate Threading/Context for "Actionable" items
        # (e.g., referring to a previous email in the loop)
        if category == "Actionable" and i > 5:
            prev_email = emails[i-random.randint(1, 5)]
            # Create a "Reply" chain simulation
            if "Ref:" not in template[0]: 
                body = f"{template[1]}\n\n> Previous Context: Regarding '{prev_email['subject']}' sent earlier..."
            else:
                body = template[1]
        else:
            body = template[1]

        email = {
            "id": 1000 + i,
            "category_ground_truth": category, # For testing, hidden from AI
            "sender": f"user{random.randint(1,50)}@example.com",
            "subject": f"{subject_prefix}{template[0]}",
            "body": body,
            "received": (datetime.now() - timedelta(minutes=i*5)).strftime("%H:%M")
        }
        emails.append(email)
        
    return emails