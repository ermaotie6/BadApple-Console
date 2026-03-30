import pickle
import gzip
import time
import sys
import os
import ctypes

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
    # 1. 窗口初始化
    os.system("cls") # 清屏
    os.system("")    # 触发 Windows 终端 ANSI 转义序列支持

    # 2. 定位资源
    data_path = get_resource_path("data/video_data.dat")
    midi_path = get_resource_path("assets/bad_apple.mid")

    if not os.path.exists(data_path):
        print(f"致命错误: 找不到数据文件 {data_path}")
        return

    # 3. 加载预处理后的视频数据
    print("正在加载数据，请稍候...")
    with gzip.open(data_path, 'rb') as f:
        width, height, frames = pickle.load(f)

    # 4. 准备音频
    # 使用绝对路径并加双引号，防止路径空格导致 MCI 失效
    midi_abs = os.path.abspath(midi_path)
    mci_send(f"open \"{midi_abs}\" alias music")

    print(f"分辨率: {width}x{height} | 帧数: {len(frames)}")
    print(">>> 已准备就绪，按 [Enter] 开始音画同步播放 <<<")
    input()

    # 5. 启动播放
    total_frames = len(frames)
    fps = 30.0
    duration = total_frames / fps # 总时长
    start_time = time.perf_counter()
    mci_send("play music")

    try:
        while True:
            elapsed = time.perf_counter() - start_time
            target_frame_idx = int(elapsed * fps)

            if target_frame_idx >= total_frames:
                break

            # --- 1. 渲染视频帧 ---
            frame = frames[target_frame_idx]
            screen_buffer = ["".join(["#" if pixel else " " for pixel in row]) for row in frame]
            
            # --- 2. 构造进度条 ---
            progress = (target_frame_idx + 1) / total_frames
            bar_length = 40 # 进度条的总宽度
            filled_length = int(bar_length * progress)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)
            
            curr_time_str = format_time(elapsed)
            total_time_str = format_time(duration)
            
            progress_line = f"\n[{bar}] {progress*100:4.1f}% | {curr_time_str} / {total_time_str}"
            
            # --- 3. 一次性合并输出 ---
            # 把视频内容和进度条拼在一起，减少 sys.stdout.write 的调用次数
            output = "\033[H" + "\n".join(screen_buffer) + progress_line
            
            sys.stdout.write(output)
            sys.stdout.flush()

            # --- 4. 动态休眠 ---
            next_frame_time = (target_frame_idx + 1) / fps
            sleep_time = next_frame_time - (time.perf_counter() - start_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n用户中止播放")
    finally:
        # 释放音频资源
        mci_send("stop music")
        mci_send("close music")
        print("\n播放完成。")

if __name__ == "__main__":
    play()