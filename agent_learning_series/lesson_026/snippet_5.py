import re

SYSTEM_PROMPT = """
You operate in a loop of Thought, Action, Observation.
Available Tools:
- get_word_count[text]: returns word count.
- calculate_hypotenuse[a, b]: returns hypotenuse.

Format:
Thought: [reasoning]
Action: tool_name[param1, param2]
Observation: [tool output]
"""

def parse_and_execute(llm_output: str):
    match = re.search(r"Action:\s*(\w+)\[(.*)\]", llm_output)
    if not match:
        return None
    tool_name, raw_args = match.group(1), match.group(2)
    args = [float(x.strip()) if x.strip().replace('.','',1).isdigit() else x.strip().strip("'\"") for x in raw_args.split(",") if x]
    
    if tool_name in TOOLS_REGISTRY:
        return TOOLS_REGISTRY[tool_name](*args)
    return f"Error: Tool '{tool_name}' not found."