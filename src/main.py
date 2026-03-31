import pickle
import gzip
import time
import sys
import os
import ctypes
import msvcrt

# 加载 Windows 多媒体底层库
winmm = ctypes.windll.winmm

def get_resource_path(relative_path):
    """ 处理开发环境与 PyInstaller 打包后的路径兼容性 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 运行时的临时解压目录
        return os.path.join(sys._MEIPASS, relative_path)
    
    # 开发环境下，基于当前脚本所在位置定位
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    
    # 根据你的项目结构进行拼接
    if "data" in relative_path:
        return os.path.join(project_root, "data", os.path.basename(relative_path))
    elif "assets" in relative_path:
        return os.path.join(project_root, "assets", os.path.basename(relative_path))
    return os.path.join(project_root, relative_path)

def mci_send(command):
    """ 执行 MCI 命令并检查 Windows 系统返回的错误信息 """
    buffer = ctypes.create_unicode_buffer(255)
    error_code = winmm.mciSendStringW(command, buffer, 255, 0)
    if error_code != 0:
        err_msg = ctypes.create_unicode_buffer(255)
        winmm.mciGetErrorStringW(error_code, err_msg, 255)
        print(f"\n[MCI Error {error_code}]: {err_msg.value}")
    return error_code

def format_time(seconds):
    """将秒数格式化为 mm:ss"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def play():
    os.system("") 
    data_path = get_resource_path("data/video_data.dat")
    midi_path = get_resource_path("assets/bad_apple.mid")

    with gzip.open(data_path, 'rb') as f:
        width, height, frames = pickle.load(f)

    midi_abs = os.path.abspath(midi_path)
    mci_send(f"open \"{midi_abs}\" alias music")
    # 强制设置时间格式为毫秒，这是音画同步的基石
    mci_send("set music time format milliseconds")

    total_frames = len(frames)
    fps = 30.0
    duration = total_frames / fps
    
    print("已就绪。 [Space]: 暂停/继续 | [Q]: 退出")
    input("按回车开始...")

    start_time = time.perf_counter()
    mci_send("play music")
    
    is_paused = False
    pause_start_time = 0
    total_pause_duration = 0 # 累计暂停的时间
    current_frame_idx = 0

    try:
        while current_frame_idx < total_frames:
            # --- 1. 处理键盘输入 (非阻塞) ---
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b' ': 
                    is_paused = not is_paused
                    if is_paused:
                        # 暂停音乐
                        mci_send("pause music")
                        pause_start_time = time.perf_counter()
                    else:
                        # --- 核心改进部分 ---
                        # 计算当前应该对应的毫秒位置
                        # elapsed 是我们逻辑上的已播放时间
                        current_ms = int((time.perf_counter() - start_time - total_pause_duration) * 1000)
                        
                        # 补偿暂停时长
                        total_pause_duration += (time.perf_counter() - pause_start_time)
                        
                        # 强制从指定毫秒位置播放
                        mci_send(f"play music from {current_ms}")
                        # -------------------
                elif key.lower() == b'q':
                    break

            if is_paused:
                time.sleep(0.1) # 暂停时降低 CPU 占用
                continue

            # --- 2. 计算当前时间 (扣除暂停时长) ---
            elapsed = time.perf_counter() - start_time - total_pause_duration
            current_frame_idx = int(elapsed * fps)

            if current_frame_idx >= total_frames:
                break

            # --- 3. 渲染画面与进度条 ---
            frame = frames[current_frame_idx]
            screen_buffer = ["".join(["#" if pixel else " " for pixel in row]) for row in frame]
            
            # 进度条逻辑
            progress = (current_frame_idx + 1) / total_frames
            bar = "█" * int(40 * progress) + "-" * (40 - int(40 * progress))
            status = " [PAUSED] " if is_paused else " [PLAYING]"
            progress_line = f"\n{status} [{bar}] {progress*100:4.1f}%"
            
            sys.stdout.write("\033[H" + "\n".join(screen_buffer) + progress_line)
            sys.stdout.flush()

            # --- 4. 同步休眠 ---
            next_frame_time = (current_frame_idx + 1) / fps
            sleep_time = next_frame_time - (time.perf_counter() - start_time - total_pause_duration)
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        mci_send("stop music")
        mci_send("close music")
        print("\n已退出播放。")

if __name__ == "__main__":
    play()