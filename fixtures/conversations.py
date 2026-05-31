CONVERSATIONS = [
    {
        "session_id": "fix-1",
        "user_id": "fixture-user",
        "messages": [
            {"role": "user", "content": "Hey, just got back from walking Biscuit. Long day at Notion."},
            {"role": "assistant", "content": "How did it go?"},
            {"role": "user", "content": "Good. I moved to Berlin from NYC two months ago. I'm vegetarian and allergic to shellfish."},
            {"role": "assistant", "content": "Berlin is great!"},
            {"role": "user", "content": "I prefer Python. Preparing for a system design interview at FAANG next week."},
        ],
        "timestamp": "2025-03-15T10:00:00Z",
    },
    {
        "session_id": "fix-2",
        "user_id": "fixture-user",
        "messages": [
            {"role": "user", "content": "Actually, I just switched jobs — now at Stripe as an engineer."},
            {"role": "assistant", "content": "Congrats!"},
        ],
        "timestamp": "2025-04-01T10:00:00Z",
    },
]

PROBES = [
    {
        "query": "Where does the user live?",
        "expected_in_context": ["Berlin"],
        "not_expected": ["Notion"],
    },
    {
        "query": "What is the user's pet name?",
        "expected_in_context": ["Biscuit"],
        "not_expected": [],
    },
    {
        "query": "Where does the user work?",
        "expected_in_context": ["Stripe"],
        "not_expected": ["Notion"],
    },
    {
        "query": "What are the user's dietary restrictions?",
        "expected_in_context": ["vegetarian", "shellfish"],
        "not_expected": [],
    },
    {
        "query": "What programming language does the user prefer?",
        "expected_in_context": ["Python"],
        "not_expected": [],
    },
]
