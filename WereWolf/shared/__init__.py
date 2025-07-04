import asyncio
import base64
import json
import logging
import os
import re
import random
import queue
import time
import boto3
from botocore.exceptions import ClientError
from anthropic import Anthropic,AnthropicBedrock
from abc import ABC, abstractmethod
from collections import Counter
from strands import Agent, tool
from strands.models import BedrockModel

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
logger = logging.getLogger(__name__)

def Info(text):
    logging.info(text)
    
def Debug(text):
    logging.debug(text)

def Warn(text):
    logging.warning(text)

def Error(text):
    logging.error(text)
    
def Print(text):
    print(text)
    
def singleton(cls):
    instances = {}
    def get_instance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return get_instance

# LANG = "cn"

def LoadMappings() -> str:
    with open("./shared/configs/lang.txt", 'r') as f:
        content = f.read()
        return content.strip()

mappings = json.loads(LoadMappings())
# print(mappings)


