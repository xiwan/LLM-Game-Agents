# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""General helper utilities the workshop notebooks"""
# Python Built-Ins:
from io import StringIO
import sys
import textwrap
import re
import json
import logging

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

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

def ParseJson(text):
    # 使用正则表达式查找 {} 之间的内容
    json_pattern = re.compile( r'{[\s\S]*?}') 
    json_strings = re.findall(json_pattern, text)
    return json_strings

def print_ww(*args, width: int = 100, **kwargs):
    """Like print(), but wraps output to `width` characters (default 100)"""
    buffer = StringIO()
    try:
        _stdout = sys.stdout
        sys.stdout = buffer
        print(*args, **kwargs)
        output = buffer.getvalue()
    finally:
        sys.stdout = _stdout
    for line in output.splitlines():
        print("\n".join(textwrap.wrap(line, width=width)))
        
def print_model_details(model):
    print("\n" + "=" * 42)
    print(f' Model: {model["modelId"]}')
    print("-" * 42)
    print(f' Name: {model["modelName"]}')
    print(f' Provider: {model["providerName"]}')
    print(f' Model ARN: {model["modelArn"]}')
    print(f' Lifecycle status: {model["modelLifecycle"]["status"]}')
    print(f' Input modalities: {model["inputModalities"]}')
    print(f' Output modalities: {model["outputModalities"]}')
    print(f' Supported customizations: {model["customizationsSupported"]}')
    print(f' Supported inference types: {model["inferenceTypesSupported"]}')
    if "responseStreamingSupported" in model:
        print(f' Response streaming supported: {model["responseStreamingSupported"]}')

    print("=" * 42)


