import asyncio
import base64
import json
import logging
import os
import re
import random
import numpy as np
import queue
import time
import boto3
from botocore.exceptions import ClientError
from anthropic import Anthropic,AnthropicBedrock
from abc import ABC, abstractmethod
from collections import Counter

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

