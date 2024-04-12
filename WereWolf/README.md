## LLM-Werewolf-EN

This is a social deduction game "Werewolf" driven by LLM models. It is mainly used to study whether mainstream LLM models can simulate human players to play the game.

### How to Run

Make sure you have Python 3.9.16 and pip 21.3.1
In this directory, run pip3 install -r requirements.txt
To start, run python3 Entry.py

### Rules 

1. The game is divided into two camps: the bad guys and the good guys. The bad guys camp only has werewolves, while the good guys camp has a witch, villagers, and a seer. Their goals are:
- Bad guys camp: Eliminate all good guys, or ensure that the number of bad guys is greater than the number of good guys.
- Good guys camp: Eliminate all bad guys, or ensure that the number of good guys is greater than the number of bad guys.

2. Item restrictions:
- The witch has only one bottle of poison and one bottle of antidote, with no replenishment after use.

3. The game alternates between night and day phases:
- At night, all players keep their eyes closed, and they can only open their eyes and take action when it's their turn.
- At night, the werewolves need to reach a unanimous vote to kill one player.
- At night, the seer can only verify the identity of one player and cannot take any other actions.
- At night, the witch can only use one bottle of antidote or poison, and it can only be used on one player.
- At night, ordinary villagers cannot take any action.
- During the day, all players open their eyes, and the phase is divided into discussion and voting rounds.
- During the day: Discussion round, every player must participate in the discussion.
- During the day: Voting round, every player must vote or abstain.


### Implementation

Currently the game contains two important modules: Game + Player

![transition-chart](./statics/transition-diagram.png)

The game module is responsible for driving the process, including:
- Initializing game configurations and players
- Controlling game pace, and invoking the player module at appropriate times to get responses
- Detecting game win conditions

The player module is responsible for communicating with the LLM. Each interaction with the game goes through the following loop:
- Memory: Extracting important logs (votes, discussions, etc) and turning them into long-term memory records of key events
- Reflect: Reflecting and summarizing based on short-term memory summaries, aiding conversation (LLM1)
- Answer: Completing character role-playing based on prompt word templates (LLM1)  
- Action: Saving important information as log entries

## LLM-Werewolf-CN

这个是基于LLM模型驱动的社交游戏《狼人杀》。主要用来研究主流LLM模型能否模拟人类玩家进行游戏。

### 如何运行它

+ 确保你有 Python 3.9.16  pip 21.3.1
+ 在此目录下运行 pip3 install -r requirements.txt
+ 启动方法 python3 Entry.py

### 规则

1.游戏分坏人和好人两大阵营, 坏人阵营只有狼人,好人阵营有女巫，村民和预言家。他们的目标为:
- 坏人阵营:消灭所有好人, 或者保证坏人数目大于好人数目
- 好人阵营:消灭所有坏人, 或者保证好人数目大于坏人数目

2.道具限制：
- 女巫只有一瓶毒药和一瓶解药，使用完后没有补充

3.游戏分白天和晚上两个阶段交替进行:

- 晚上所有玩家闭眼，轮到自己才可以睁眼行动
- 晚上狼人需要达成统一投票杀死一名玩家
- 晚上预言家只能查验一名玩家身份,无法有其他行动
- 晚上女巫每个晚上只能用一瓶解药或者毒药, 并且只能对一名玩家使用
- 晚上普通村民晚上无法行动
- 白天所有玩家睁眼, 分为讨论和投票两环节
- 白天:讨论环节，每个玩家必须参与讨论
- 白天:投票环节，每个玩家必须投票或者放弃

### 实现

#### 第一个版本

为了简单，第一个版本的法官由程序控制，玩家为LLM配置，采用**2狼+1预言家+1女巫+4村民**的模式, 具体的配置如下:

~~~
[{"id": 1001, "name": "P1", "role": "预言家", "character": "独立思考", "status": 1}, {"id": 1002, "name": "P2", "role": "女巫", "character": "腼腆型", "status": 1}, {"id": 1003, "name": "P3", "role": "狼人", "character": "组织者", "status": 1}, {"id": 1004, "name": "P4", "role": "村民", "character": "规矩型", "status": 1}, {"id": 1005, "name": "P5", "role": "村民", "character": "话痨", "status": 1}, {"id": 1006, "name": "P6", "role": "狼人", "character": "过激型", "status": 1}, {"id": 1007, "name": "P7", "role": "村民", "character": "观察家", "status": 1}, {"id": 1008, "name": "P8", "role": "村民", "character": "互动达人", "status": 1}]
~~~

游戏的框架还是由程序驱动，会在规定的时间几点调用以下问题模版，比如:
~~~
{
    "player": {
        "action_plan_night": "{0} {1} 现在是第{2}天夜晚，该如何行动?",
        "action_plan_day": "{0} {1} 现在是第{2}天白天的讨论环节，该如何行动?",
        "action_plan_day_vote": "{0} {1} 现在是第{2}天白天的投票环节，该如何行动?",
        "action_plan_death": "现在是第{0}天白天，玩家已经死亡,有何遗言?",
        "action_confirm": "收到",
        "action_villager_team": "未知,需要你推理发现.",
        "action_reflect": "{0} {1} 该如何思考?",
        "action_plan_test": "现在全场几人活着几人淘汰"
    },
    "god": {
        "action_plan_night": "{0}现在是第{1}天夜晚，你该如何行动？",
        "action_plan_day": "{0}现在是第{1}天白天，你该如何行动？",
        "action_plan_test": "现在全场几人活着几人淘汰"
    },
    "system": {
        "death_night": "昨晚, 玩家{0}被狼人淘汰, 遗言为:{1}.",
        "death_day": "今天, 玩家{0}被玩家淘汰, 遗言为:{1}.",
        "win_wolf": "狼人胜利!",
        "win_villager": "村民胜利!",
        "win_none": "游戏继续. 目前玩家存活情况:{0}",
        "board": "现在玩家存活情况:{0}"
    }
}
~~~
+ 其中 **player** 模块为针对玩家LLM提出的问题
+ 其中 **god** 模块为针对上帝LLM提出的问题（TBD）
+ 其中 **system** 模块为系统消息，会广播给所有的LLM

#### 模块

目前游戏包含两个重要模块: 游戏 + 玩家

![transition-chart](./statics/transition-diagram.png)

游戏模块负责驱动进程，包括
+ 初始化游戏配置以及玩家
+ 控制游戏节奏，在合适的时间点调用玩家模块来获取回答
+ 检测游戏胜利条件

玩家模块负责和LLM通讯, 每次和游戏交互需要经过以下循环:
+ 记忆: 提取重要日志（投票，讨论等），变成长期记忆记录关键事件
+ 推理: 根据短期记忆的总结，进行反思和总结, 辅助对话(LLM1)
+ 对话: 基于提示词模版完成角色带入(LLM1)
+ 行动: 是将重要信息存为日志*


