import pickle
import gzip
import time
import sys
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def play():
    # 初始化 Windows 终端支持
    os.system("") 
    
    data_path = resource_path("video_data.dat")
    if not os.path.exists(data_path):
        print("未找到数据文件！")
        return

    with gzip.open(data_path, 'rb') as f:
        width, height, frames = pickle.load(f)

    print("准备就绪，按回车开始播放...")
    input()

    for frame in frames:
        # 核心逻辑：将布尔阵列转为字符
        output = []
        for row in frame:
            line = "".join(["#" if pixel else " " for pixel in row])
            output.append(line)
        
        # 刷新屏幕
        sys.stdout.write("\033[H" + "\n".join(output))
        sys.stdout.flush()
        
        # 根据原视频帧率调整（Bad Apple 一般是 30fps）
        time.sleep(1/30)

if __name__ == "__main__":
    play()