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
with open("cse476-final/cse476_final_project_dev_data.json", "r") as f:
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
    You are an assistant that is only allowed to output the final answer and nothing else.
    Never provide reasoning.
    Never provide chain of thought.
    If the answer is a number, provide ONLY the answer number.
    If the answer is a word, provide ONLY the asnwer word.
    Do not say "The answer is" or anything of the like.
    If the problem is a math problem, ONLY give the final answer.
    If the problem is a chinese math problem, ONLY give the final answer and nothing else.
    """
    prompt = f"""
    Give ONLY the final answer.
    Never provide reasoning.
    If the answer is anumber, give only the number.
    Question: {question}
    """

    result = call_model_chat_completions(prompt, system=system, model=MODEL, temperature=0.2)
    result = result["text"]
    
    #print(result)
    
    # Removing $ from math outputs
    if result.startswith("$") and result.endswith("$"):
        result = result[1:-1].strip()

    return result

#print(dev_data[2])
#test_question = "汤米正在通过卖布朗尼蛋糕（每块 3 美元）和芝士蛋糕（每块 4 美元）为自己的慈善组织筹款。如果汤米卖出了 43 块布朗尼蛋糕和 23 块芝士蛋糕，他筹到了多少钱？"
#print(chain_of_thought(test_question))

def self_consistency(question, steps=7):
    result_list = []

    for _ in range(steps):
        result_list.append(chain_of_thought(f"Do not provide any reasoning. Question: {question}"))

    clean_result_list = [c.strip() for c in result_list]
    counter = Counter(clean_result_list)
    return counter.most_common(1)[0][0]

def verify(question):
    system = f"""
    You are a concise verifier.
    Provide only the final answer.
    Do not show reasoning or chain of thought.
    """

    prompt = f"""
    Question: {question}
    Answer:
    """

    result = call_model_chat_completions(prompt, system=system, model=MODEL, temperature=0.0)
    text = result["text"].strip()
    return text


def decomp(question):
    system = """
    Break the problem into smaller steps and solve step by step but never provide the steps.
    Never give explanations.
    Answer with only the final answer and nothing else.
    """
    
    prompt = f"""
    Question: {question}
    """
    result = call_model_chat_completions(prompt, system=system, model=MODEL, temperature=0.1)
    return result["text"].strip()

def agent(question):
    cot_ans = chain_of_thought(question)
    sc_ans = self_consistency(question, steps=2)
    decomp_ans = decomp(question)

    answers = [cot_ans, sc_ans, decomp_ans]

    #print(answers)

    if answers[0] == answers[1] == answers[2]:
        return answers[0]
    
    if answers[1] == answers[0] or answers[1] == answers[2]:
        return answers[1]
    
    return answers[0]
    
#print(agent(test_question))

# %%


"""
References
- Self Consistency: https://www.promptingguide.ai/techniques/consistency
"""