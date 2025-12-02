# %% Minimal setup
# If needed (uncomment in a notebook):
# !pip install requests python-dotenv

import os, json, textwrap, re, time
import requests
from collections import Counter

API_KEY  = "cse476"
API_BASE = "http://10.4.58.53:41701/v1"
MODEL    = "bens_model"

def call_model_chat_completions(prompt: str,
                                system: str = "You are a helpful assistant. Reply with only the final answer—no explanation.",
                                model: str = MODEL,
                                temperature: float = 0.0,
                                timeout: int = 60) -> dict:
    """
    Calls an OpenAI-style /v1/chat/completions endpoint and returns:
    { 'ok': bool, 'text': str or None, 'raw': dict or None, 'status': int, 'error': str or None, 'headers': dict }
    """
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 128,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        status = resp.status_code
        hdrs   = dict(resp.headers)
        if status == 200:
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"ok": True, "text": text, "raw": data, "status": status, "error": None, "headers": hdrs}
        else:
            # try best-effort to surface error text
            err_text = None
            try:
                err_text = resp.json()
            except Exception:
                err_text = resp.text
            return {"ok": False, "text": None, "raw": None, "status": status, "error": str(err_text), "headers": hdrs}
    except requests.RequestException as e:
        return {"ok": False, "text": None, "raw": None, "status": -1, "error": str(e), "headers": {}}


# Dev Data for Testing
with open("cse476_final_project_dev_data.json", "r") as f:
    dev_data = json.load(f)

"""
Agent Code:

Chain of Thought
Self Consistency
Try ReAcT

Move these into a loop instead of separate functions

"""

system = "You are a helpful multi use agent. Do not explain the reasoning behind the answer, do not include anything but the final answer."

def chain_of_thought(question):
    prompt = f"Give only the exact answer, do not include anything but the answer: {question}"
    result = call_model_chat_completions(prompt, system=system, model=MODEL, temperature=0.1)
    result = result["text"]
    
    # Removing $, pretty sure this is just a math delimitter
    if result.startswith("$") and result.endswith("$"):
        result = result[1:-1].strip()

    return result

#print(chain_of_thought((dev_data[0])['input']))

def self_consistency(question, steps=7):
    result_list = []

    for _ in range(steps):
        result_list.append(chain_of_thought(question).strip())

    clean_result_list = [c.strip() for c in result_list]
    counter = Counter(clean_result_list)
    return counter.most_common(1)[0][0]

#print(self_consistency((dev_data[0])['input']))

# %%


"""
References
- Self Consistency: https://www.promptingguide.ai/techniques/consistency
"""