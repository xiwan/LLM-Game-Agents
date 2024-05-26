import sys
from shared.GameServer import GameServer

if __name__ == "__main__":
    # 打印所有命令行参数
    print("Command line arguments:", sys.argv)
    round_value = 50
    qsize_value = 50
    # 遍历命令行参数
    for arg in sys.argv[1:]:  # 从索引1开始,跳过脚本名称
        if arg.startswith("--round="):
            round_value = int(arg.split("=")[1])
        elif arg.startswith("--qsize="):
            qsize_value = int(arg.split("=")[1])
            
    print("Round value:", round_value)
    print("Queue size:", qsize_value)
    GS = GameServer(round_value, qsize_value)
    GS.Run("0.0.0.0", 8000)
