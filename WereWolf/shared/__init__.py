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
    
def singleton(cls):
    instances = {}
    def get_instance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return get_instance

# LANG = "cn"

mappings = {
    'wolf': {'en': 'wolf','cn': '狼人'},
    'witch': {'en': 'witch','cn': '女巫'},
    'prophet': {'en': 'prophet','cn': '预言家'},
    'villager': {'en': 'villager','cn': '村民'},
    'status_alive':  {'en': 'alive','cn': '存活'},
    'status_eliminated':  {'en': 'eliminated','cn': '淘汰'},
    'playerInfoBuilder': {'en': 'Team: {0}. Teammates Unkown.', 'cn': '阵营为:{0}.本阵营队友未知.'},
    'playerStateInfoBuilder': {
        'en': 'Current state:{0}.', 
        'cn': '目前玩家状态:{0}.'},
    'playerDoAnswer': {
        'en': 'Score from the previous round of decision-making: {0}. It is recommended to adjust the strategy.', 
        'cn': '上轮决策评分:{0}.建议调整策略.'},
    'playerDoReflect': {
        'en': 'Game progress: {1}. Player information: {2}. Time: {0}. Player decision: {3}.', 
        'cn': '游戏进度:{1}.玩家信息:{2}. 时间:{0}.玩家决策:{3}.'},
    'prophetUseAbility': {
        'en': 'Player {0} role/identity is {1}.', 
        'cn': '玩家{0}身份是{1}.'},
    'wolfInfoBuilder': {
        'en': 'Team: {0}. Teammates: {1}.', 
        'cn': '阵营为:{0}.本阵营队友{1}.'},
    'witchInfoBuilder': {
        'en': 'Potion status: Poison {0}, Antidote {1}. Each night you can use a potion to save someone or save yourself (time: {2} eliminated players), or eliminate a player (time: {2} surviving players).', 
        'cn': '药水情况: 毒药{0},解药{1}.每晚可以使用药水救人或者自救(时间:{2}淘汰的玩家),或者淘汰某玩家(时间:{2}存活的玩家).'},
    "WitchPoision": {
        'en': 'Time {0}, Player {1} was poisoned to death by the Witch.', 
        'cn': '时间{0}, 玩家{1}被女巫毒死',
    },
    "WitchAntidote": {
        'en': 'Time {0}, Player {1} was revived by the Witch.', 
        'cn': '时间{0}, 玩家{1}被女巫救活',
    },
    'MasterCheckWinner': {
        'en': 'Time {0}, Survival status: Bad: {1}, Good: {2}.',
        'cn': '时间{0},场上存活状态 坏人:{1} 好人:{2}.'
    },
    'MasterVote': {
        'en': 'Time {0}, Player {1} was eliminated.',
        'cn': '"时间{0},玩家{1}被淘汰."'
    }
    
}


