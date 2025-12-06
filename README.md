# CSE 476 Agent
To use the agent, simply pass in a question to the agent() function
    print(agent(question)) for example

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

The first thing I needed to find out was what techniques I wanted to implement. I decided to go with Chain of Thought, Self Consistency and Decomposition. The agent works by calling all of these functions, with a step size of 2 generations for self consistency for speed, storing then into an array and comparing the answers. During testing I had realized that each of these functions were providing very different answers, so within the agent function I added a check that would be able to see if the answers were similar within the generations and if they werent, then the fallback returns the chain of thought.


## Chain of Thought
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

For Chain of Thought, I instructed the system to provide only the final and nothing else. But some of the answers are still coming out with a reasoning chain attatched to it. Mostly with math problems, I could not find a way that would 100% circumvent this but it works for the most part. After the system prompt and prompt input from the function, we run the function prompt through the call_model_chat() function that was provided from the tutorial, get the text output from the model and I had noticed that the math outputs would sometimes have a $ at the beginning and at the end. So I implemented a check to see if the result starts or ends with a $ and remove them.

## Self Consistency
    def self_consistency(question, steps=7):
        result_list = []

        for _ in range(steps):
            result_list.append(chain_of_thought(f"Do not provide any reasoning. Question: {question}"))

        clean_result_list = [c.strip() for c in result_list]
        counter = Counter(clean_result_list)
        most_common = counter.most_common(1)[0][0]
        return most_common


For self consistency, I implemented a function that takes a question and steps as input, then it is ran through a loop steps times, which then calls chain of thought. This will give us steps different calls to the llm to give us more answeres to work with. I then cleaned the list by stripping the outputs and initializing a counter to count the occurences in the array and then returning the value.


## Decompostion
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
        result = result["text"].strip()
        return result

The decomposition function is essentially just calling the model with the new system prompt and returning the stripped result. This prompt instructs the model to try and break the model into smaller segments and solve the problem without giving chain of thought output.
