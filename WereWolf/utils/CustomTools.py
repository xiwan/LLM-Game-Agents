import datetime
import json
import re
import os
from typing import List, Union
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error

# Langchain imports
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.agents import AgentExecutor, create_structured_chat_agent, create_react_agent
from langchain.prompts import BaseChatPromptTemplate, ChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, HumanMessage, SystemMessage
from langchain import SerpAPIWrapper, LLMChain

# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
            
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        kwargs["nickname"] = "P1"
        kwargs["role"] = "平民"
        kwargs["character"] = "冲动"
        formatted = self.template.format(**kwargs)
        print(formatted)
        return [HumanMessage(content=formatted)]


    
class CustomOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        response = ParseJson(llm_output)
        for res in response:
            res_obj = json.loads(res)
            action = res_obj["action"]
            action_input = res_obj["target"] if "target" in res_obj else ""
            
            # Return the action and action input
            return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
        
        raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        
        
#         # Check if agent should finish
#         if "Final Answer:" in llm_output:
#             return AgentFinish(
#                 # Return values is generally always a dictionary with a single `output` key
#                 # It is not recommended to try anything else at the moment :)
#                 return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
#                 log=llm_output,
#             )
        
#         # Parse out the action and action input
#         regex = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
#         match = re.search(regex, llm_output, re.DOTALL)
        
#         # If it can't parse the output it raises an error
#         # You can add your own logic here to handle errors in a different way i.e. pass to a human, give a canned response
#         if not match:
#             raise ValueError(f"Could not parse LLM output: `{llm_output}`")
#         action = match.group(1).strip()
#         action_input = match.group(2)
        
#         # Return the action and action input
#         return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
    