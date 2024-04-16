from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .GameAssistant import GameAssistant
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerWolf(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)

    def _playerInfoBuilder(self):
        extraInfo = "本阵营玩家为:{0}.".format(GetAllWolvesName())
        playerInfo = game_config_dict["player"]["action_prefix"].format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        return playerInfo 