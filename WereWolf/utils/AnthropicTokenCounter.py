from langchain.callbacks.base import BaseCallbackHandler

import boto3

class AnthropicTokenCounter(BaseCallbackHandler):
    def __init__(self, llm):
        self.llm = llm
        self.input_tokens = 0
        self.output_tokens = 0


    def on_llm_start(self, serialized, prompts, **kwargs):
        for p in prompts:
            self.input_tokens += self.llm.get_num_tokens(p)


    def on_llm_end(self, response, **kwargs):
        results = response.flatten()
        for r in results:
            self.output_tokens = self.llm.get_num_tokens(r.generations[0][0].text)