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
    start_time = time.perf_counter()
    mci_send("play music")

    try:
        while True:
            # 计算当前音频时间对应的帧索引（Master Clock 同步逻辑）
            elapsed = time.perf_counter() - start_time
            target_frame_idx = int(elapsed * fps)

            # 检查是否播放完毕
            if target_frame_idx >= total_frames:
                break

            # 渲染当前帧（跳过落后帧，实现 Drop Frame 同步）
            frame = frames[target_frame_idx]
            
            # 构造整帧字符串，一次性写入 stdout 减少 I/O 耗时
            # \033[H 将光标重置到左上角 (0,0) 实现无闪烁刷新
            screen_buffer = ["".join(["#" if pixel else " " for pixel in row]) for row in frame]
            output = "\033[H" + "\n".join(screen_buffer)
            
            sys.stdout.write(output)
            sys.stdout.flush()

            # 动态休眠：计算距离下一帧渲染的时间间隔
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