import cv2
import pickle
import gzip

def generate_data(video_path, width=80):
    cap = cv2.VideoCapture(video_path)
    frames_data = []
    
    # 获取比例
    original_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    original_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    height = int((original_height / original_width) * width / 2)

    print(f"开始预处理视频: {width}x{height}...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # 缩放、灰度、二值化
        resized = cv2.resize(frame, (width, height))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # 将矩阵转为布尔型（True/False）以节省空间
        bool_frame = (binary == 255).tolist()  # 转为列表以便序列化
        frames_data.append(bool_frame)

    cap.release()

    # 使用 gzip 压缩并序列化
    with gzip.open('video_data.dat', 'wb') as f:
        pickle.dump((width, height, frames_data), f)
    print("预处理完成！生成了 video_data.dat")

if __name__ == "__main__":
    generate_data("badapple.mp4") # 确保你的视频文件名正确