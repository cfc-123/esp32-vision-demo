import cv2
import serial
import numpy as np
import time

# ================= 配置区 =================

SERIAL_PORT = 'COM7'
BAUD_RATE = 115200
# ==========================================

# 加载 OpenCV 自带的人脸检测模型
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 初始化串口
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
print(f"串口 {SERIAL_PORT} 已打开，等待接收图像数据...")

# 用于拼接串口数据的缓冲区
img_bytes = b''
receiving = False

try:
    while True:
        # 读取串口数据
        data = ser.read(1024)
        
        if data:
            # JPEG 图片的开始标志是 0xFFD8，结束标志是 0xFFD9
            if b'\xff\xd8' in data:
                receiving = True
                img_bytes = b'' # 清空缓冲区准备重新接收
            
            if receiving:
                img_bytes += data
            
            if b'\xff\xd9' in data and receiving:
                receiving = False
                print(f"接收到一帧图片，大小: {len(img_bytes)} 字节")
                
                # 将字节流转换成 OpenCV 图片格式
                nparr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # 转灰度图（提升检测速度）
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # 检测人脸
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                    
                    # 获取画面中心坐标
                    h, w = frame.shape[:2]
                    center_x, center_y = w // 2, h // 2
                    
                    for (x, y, fw, fh) in faces:
                        # 画框
                        cv2.rectangle(frame, (x, y), (x+fw, y+fh), (0, 255, 0), 2)
                        # 计算人脸中心
                        face_cx = x + fw // 2
                        face_cy = y + fh // 2
                        cv2.circle(frame, (face_cx, face_cy), 5, (0, 0, 255), -1)
                        
                        # 计算偏差（用于后续控制云台/机械臂）
                        dx = face_cx - center_x
                        dy = face_cy - center_y
                        print(f"目标坐标偏差 -> X: {dx}, Y: {dy}")
                    
                    # 显示画面
                    cv2.imshow('ESP32 Vision Tracking', frame)
                
                # 清空数据准备下一帧
                img_bytes = b''
                
        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
except KeyboardInterrupt:
    print("程序已退出")
finally:
    ser.close()
    cv2.destroyAllWindows()