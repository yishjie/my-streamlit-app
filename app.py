import streamlit as st
import cv2
import numpy as np
from PIL import Image

# 设置页面标题和布局
st.set_page_config(page_title="AI 视频助手", layout="wide")

st.title("🎥 我的 AI 视频助手")
st.markdown("上传一个视频，我将为你提取关键帧并展示。")

# 侧边栏：文件上传
st.sidebar.header("上传视频")
uploaded_file = st.sidebar.file_uploader("选择一个视频文件...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # 显示上传成功的提示
    st.success("视频上传成功！正在处理...")
    
    # 将上传的文件转换为 OpenCV 可读的格式
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    video = cv2.VideoCapture(cv2.imdecode(file_bytes, 1))
    
    # 获取视频基本信息
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    st.info(f"视频信息：时长 {duration:.2f} 秒 | 帧率 {fps:.2f} FPS | 总帧数 {total_frames}")

    # 创建一个滑块来选择要显示的帧
    frame_number = st.slider("选择要查看的帧数", 0, total_frames - 1, 0)
    
    # 跳转到指定帧
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    
    if ret:
        # 将 BGR (OpenCV) 转换为 RGB (Streamlit/PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.image(frame_rgb, caption=f"第 {frame_number} 帧", use_column_width=True)
        
        # 添加一个简单的“分析”按钮（模拟功能）
        if st.button("✨ 分析这一帧"):
            st.write("正在分析画面内容... (此处可接入 AI 模型)")
            st.balloons()
    else:
        st.error("无法读取该帧。")

    video.release()
else:
    st.info("👈 请在左侧上传视频以开始。")

# 页脚
st.markdown("---")
st.caption("Powered by Streamlit & OpenCV")