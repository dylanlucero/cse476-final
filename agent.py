# %% Minimal setup
# If needed (uncomment in a notebook):
# !pip install requests python-dotenv

import os, json, textwrap, re, time
import requests
from collections import Counter

from sympy import resultant

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

def chain_of_thought(question):
    system = f"""
    You are a reasoning assistant. 
    Think step by step but do not explain the reasoning.
    Give only the final answer, do not include any explanations.
    """
    
    prompt = f"""
    Question: {question}
    """

    result = call_model_chat_completions(prompt, system=system, model=MODEL, temperature=0.1)
    ########
    #This is spewing a None Type Error when called from agent loop
    result = result["text"]
    #######
    
    print(type(result))
    
    # Removing $, pretty sure this is just a math delimitter
    if result.startswith("$") and result.endswith("$"):
        result = result[1:-1].strip()

    return result

#print(dev_data[2])
#print(chain_of_thought((dev_data[2])['input']))

def self_consistency(question, steps=7):
    result_list = []

    for _ in range(steps):
        result_list.append(chain_of_thought(question).strip())

    clean_result_list = [c.strip() for c in result_list]
    counter = Counter(clean_result_list)
    return counter.most_common(1)[0][0]

def verify(question, answer):
    system = f"""
    You are a deterministic verifier.
    Answer with only "Yes" or "No". Do not give explanations.
    """

    prompt = f"""
    Question: {question}
    Answer: {answer}
    
    Is this answer completely correct?
    """

    result = call_model_chat_completions(prompt, system=system, model=MODEL, temperature=0)
    text = result["text"].strip()
    if text.startswith("Yes"):
        return "Yes"
    else:
        return "No"

def decomp(question):
    system = """
    Break the problem into smaller steps and solve step by step.
    Do not give the reasoning explanation.
    Answer with only the final answer.
    """
    
    prompt = f"""
    Question: {question}
    """
    result = call_model_chat_completions(question, system=system, model=MODEL, temperature=0.1)
    return result["text"].strip()

# Function is failing at self consistency
def agent(question):
    sc_ans = self_consistency(question, 5)
    expected_ans = (dev_data[2])["output"]
    print("Pass self consistency")

    correct = verify(sc_ans, expected_ans)

    if correct == "Yes":
        return sc_ans

    print("answer was incorrect")  
    decomp_ans = decomp(question)

    correct = verify(decomp_ans, expected_ans)

    if correct == "Yes":
        return decomp_ans

    return chain_of_thought(question)
    


# SC is now broken, AttributeError: 'NoneType' object has no attribute 'strip'
print(agent((dev_data[2])['input']))

# %%


"""
References
- Self Consistency: https://www.promptingguide.ai/techniques/consistency
"""