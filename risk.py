import anthropic
import os
from dotenv import load_dotenv
import json
load_dotenv()
def assess_risk(sender_balance: int, receiver_balance: int, amount: int) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  
    prompt = f"""
    You are a fraud detection engine.
    
    Transaction details:
    - Sender balance: {sender_balance} pence
    - Receiver balance: {receiver_balance} pence
    - Amount being sent: {amount} pence
    - Percentage of balance being sent: {round(amount/sender_balance * 100, 2)}%
    
    YOUR TASK: Analyse and give a score between 0-100 of the transfer based on the transaction details above.
    RESPONSE FORMAT: Respond with raw JSON only. Do NOT use markdown. Do NOT wrap in backticks or code fences. Output ONLY the JSON object, nothing else:
        {{
            "risk_score": (0-100),
            "reasoning": "brief explanation",
            "decision": "approve" or "block"
        }}
    """

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    print(raw)
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]  
        raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()
    result = json.loads(raw)

    return result 