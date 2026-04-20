import anthropic
import json

def assess_risk(sender_balance: int, receiver_balance: int, amount: int) -> dict:
    client = anthropic.Anthropic(api_key="your-api-key")
    
    prompt = f"""
    You are a fraud detection engine.
    
    Transaction details:
    - Sender balance: {sender_balance} pence
    - Receiver balance: {receiver_balance} pence
    - Amount being sent: {amount} pence
    - Percentage of balance being sent: {round(amount/sender_balance * 100, 2)}%
    
    YOUR TASK: Analyse and give a score between 0-100 of the transfer based on the transaction details above.
    RESPONSE FORMAT: You must respond only in JSON with no extra text, no markdown, no backticks.Return exactly this JSON structure:
        {
            "risk_score": (0-100),
            "reasoning": "brief explanation",
            "decision": "approve" or "block"
        }
    """

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    result = json.loads(response.content[0].text)

    return result