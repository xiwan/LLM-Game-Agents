from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerProphet(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)
        self.checkList = {}

    def _getPlayerRole(self, name) -> str:
        for player in self.GM.roles_dict["players"]:
            if EqualIgnoreCase(player["name"],name):
                return (name, player["role"])
                # return "{0}:{1}".format(name, player["role"])
        return (None, None)
    
    def _checkPlayer(self, action_time, name, role):
        # 检查当前轮数是否已经存在记录
        if action_time in self.checkList and self.checkList[action_time]:
            Info(f"Error: Round {action_time} already has a record {name}:{role}.")
            return False
        # 创建新的内层字典,并将玩家编号和身份存储进去
        self.checkList[action_time] = {name: role}
        Info(self.checkList)
        return True
    
    def _playerInfoBuilder(self):
        extraInfo = self.GM.Lang("playerInfoBuilder").format(GetPartySize(self.GM.roles_dict, self.GM.lang))
        #playerInfo = self.GM.game_config_dict["player"]["action_prefix"].format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        playerInfo = self.GM.Lang("player.action_prefix").format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        return playerInfo
    
    def DoMemory(self, memorysize=10, memories=[]):
        
        for log in self.GM.game_prophet_check_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))
        memories = super().DoMemory(memorysize, memories)
        return memories

    def UsePlayerAbility(self, abilityName, target=None, item=None):
        log = super().UsePlayerAbility(abilityName, target, item)
        if self.GM.isDay or target is None:
            return None

        if EqualIgnoreCase(abilityName, "ProphetCheck"):
            name, role= self._getPlayerRole(target)
            if name is None or role is None:
                return log
            
            if not self._checkPlayer(item["action_time"], name, role):
                return log
            
            # self.checkList.append(checker)
            checker = self.GM.Lang("prophetUseAbility").format(name, role)
            self.GM.game_prophet_check_log.append(checker)
            log = ReadableActionLog("prophet_check_log", self.GM.current_time, self.agent["name"], item)
            self.AddMemory(log)
            self.GM.prophetVotes[-1].vote(target)
        return log