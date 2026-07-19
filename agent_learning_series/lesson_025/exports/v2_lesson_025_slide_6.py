import re

class ReActAgent:
    def __init__(self, llm_client, tools):
        self.llm = llm_client
        self.tools = tools
        self.system_prompt = """
        You operate in a loop of Thought, Action, Observation.
        Use Thought to describe your thoughts about the question.
        Use Action to run one of the available tools: {tool_names}
        Observation will be the result of running those tools.
        """.format(tool_names=list(tools.keys()))

    def run(self, user_query, max_iterations=5):
        history = [{"role": "system", "content": self.system_prompt},
                   {"role": "user", "content": user_query}]
        
        for i in range(max_iterations):
            response = self.llm.complete(history)
            print(f"\n[LLM Output - Iteration {i+1}]\n{response}")
            history.append({"role": "assistant", "content": response})
            
            action_match = re.search(r"Action:\s*(\w+)\[(.*)\]", response)
            if action_match:
                tool_name, tool_arg = action_match.groups()
                if tool_name in self.tools:
                    obs = self.tools[tool_name](tool_arg)
                    print(f"[System Tool Output] Observation: {obs}")
                    history.append({"role": "user", "content": f"Observation: {obs}"})
                else:
                    history.append({"role": "user", "content": f"Observation: Tool {tool_name} not found."})
            else:
                # No tool action found, agent has finalized response
                break