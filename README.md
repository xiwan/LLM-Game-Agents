# LLM-Game-Agents

This is a repo for studying the application of LLM Agents on Games

## Description

There are usually 4 types of intervention methods for LLM models:

![cost-complexity](./WereWolf/statics/cost-complexity.png)

+ Prompt Engineering: Using prompt templates to guide the LLM's output.
+ RAG: Typically interfaced with a vector database. 
+ Fine-Tuning: Not training the full model, can be analogous to LoRA.
+ Pre-Training: Specifically pre-training the large model.

Among these, Prompt Engineering has the best cost-performance ratio. Here we will mainly use langchain to complete LLM's contextual awareness and logical reasoning abilities.


## LLM-Werewolf-EN

This is a social deduction game "Werewolf" driven by LLM models. It is mainly used to study whether mainstream LLM models can simulate human players to play the game.

### Rules 

**Role Assignment**:
There are only two roles - villagers and werewolves. At the start of the game, the moderator randomly assigns players as villagers or werewolves.

**Night Phase**:
Only the werewolves have a kill action. Werewolves decide which player to kill.

**Day Phase**:
1. Players discuss and vote: All players discuss then vote to eliminate one player.
2. Check for deaths: The moderator confirms players that died the previous night.

**Game End Conditions**:
1. If the number of werewolves is equal to or greater than villagers, the werewolves win.
2. If the number of villagers equals the werewolves, the villagers win.

## LLM-Werewolf-CN

这个是基于LLM模型驱动的社交游戏《狼人杀》。主要用来研究主流LLM模型能否模拟人类玩家进行游戏。

### 规则

**角色分配**:
只有两种角色 - 村民和狼人。游戏开始时,法官随机分配玩家为村民或狼人。

**夜晚阶段**:
只有狼人的杀人行动。狼人可以决定杀死一名玩家。

**白天阶段**:
1. 玩家讨论和投票:所有玩家进行讨论,然后投票决定淘汰一名玩家。
2. 检查死亡:法官确认前一晚死亡的玩家。

**游戏结束条件**:
1. 狼人的数量等于或多于村民,狼人胜利。
2. 村民的数量等于狼人数量,村民胜利。



