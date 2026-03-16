import streamlit as st
import cv2
import tempfile
import os
import time

# 设置页面配置
st.set_page_config(page_title="AI 视频助手", layout="wide")

st.title("🎬 我的 AI 视频助手 (增强版)")
st.markdown("""
上传任意标准 **MP4** 视频，系统将自动提取关键帧。
*已优化编码兼容性，支持 H.264/H.265 封装的 MP4*
""")

uploaded_file = st.file_uploader("选择一个 MP4 视频文件...", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    # 1. 创建临时文件
    # 使用 delete=False 手动管理生命周期，确保文件完全写入
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') 
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    tfile.close()  # 关闭文件句柄，确保数据落盘

    st.info(f"📂 文件已保存至临时路径：{video_path} (大小: {uploaded_file.size / 1024 / 1024:.2f} MB)")

    # 稍微等待一下，确保文件系统同步（针对云环境优化）
    time.sleep(0.5)

    # 2. 尝试打开视频 (增加兼容性策略)
    cap = None
    
    # 策略 A: 默认打开
    cap = cv2.VideoCapture(video_path)
    
    # 策略 B: 如果默认失败，尝试强制指定 FFMPEG 后端 (Linux 服务器常用)
    if not cap.isOpened():
        st.warning("⚠️ 默认模式打开失败，尝试切换至 FFMPEG 后端...")
        cap.release()
        cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)

    # 策略 C: 如果还不行，尝试 OPENCV 后端
    if not cap.isOpened():
        st.warning("⚠️ FFMPEG 模式失败，尝试切换至 OPENCV 原生后端...")
        cap.release()
        cap = cv2.VideoCapture(video_path, cv2.CAP_OPENCV_MJPEG) # 某些情况有效

    # 3. 最终检查
    if not cap.isOpened():
        st.error("❌ **致命错误**：无法读取该视频文件。")
        st.markdown("""
        **可能原因：**
        1. 视频文件已损坏。
        2. 视频编码极其特殊，当前服务器环境缺少对应的解码器。
        3. 文件传输过程中丢失了数据头。
        
        *建议：尝试用手机录制一个新的短视频测试，或检查文件是否在本地能正常播放。*
        """)
        # 清理临时文件
        os.unlink(video_path)
        st.stop()

    # 4. 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 计算时长
    duration = total_frames / fps if fps > 0 else 0

    # 显示成功信息
    st.success("✅ **视频解析成功！**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总帧数", total_frames)
    col2.metric("帧率 (FPS)", f"{fps:.2f}")
    col3.metric("时长 (秒)", f"{duration:.2f}")
    col4.metric("分辨率", f"{width}x{height}")

    if total_frames > 0:
        # 5. 交互式滑块
        max_frame = total_frames - 1
        frame_number = st.slider("拖动查看不同帧", 0, max_frame, 0)

        # 6. 定位并读取帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if ret:
            # OpenCV 读取的是 BGR，Streamlit 需要 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, caption=f"第 {frame_number} 帧 (时间: {frame_number/fps:.2f}s)", use_column_width=True)
        else:
            st.warning(f"⚠️ 无法读取第 {frame_number} 帧，可能是文件尾部损坏。")
            
        # 释放资源
        cap.release()
    else:
        st.warning("⚠️ 视频帧数为 0，虽然文件头被识别，但无法提取图像内容。")

    # 清理临时文件
    try:
        os.unlink(video_path)
    except:
        pass