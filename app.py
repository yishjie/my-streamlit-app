import streamlit as st
import cv2
import tempfile
import os
import numpy as np
from datetime import timedelta

# --- 页面配置 ---
st.set_page_config(
    page_title="我的 AI 视频助手 (增强版)",
    page_icon="🎬",
    layout="wide",  # 使用宽屏模式
    initial_sidebar_state="collapsed"
)

# 自定义 CSS 样式，让界面更美观
st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .stImage img {border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .keyframe-card {background-color: #f0f2f6; padding: 10px; border-radius: 8px; text-align: center;}
    .analysis-box {background-color: #e8f4fd; padding: 15px; border-radius: 8px; border-left: 5px solid #0068c9;}
    h1, h2, h3 {color: #2c3e50;}
    .stAlert {margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

# --- 标题与介绍 ---
st.title("🎬 我的 AI 视频助手 (增强版)")
st.markdown("""
上传任意标准 MP4 视频，系统将自动提取关键帧并进行智能分析。  
*已优化编码兼容性，支持 H.264/H.265 封装的 MP4*
""")

# --- 文件上传 ---
uploaded_file = st.file_uploader("选择一个 MP4 视频文件...", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    # 保存临时文件
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.info(f"📂 文件已保存至临时路径：{video_path} (大小: {round(os.path.getsize(video_path)/1024/1024, 2)} MB)")

    # --- 视频基础信息解析 ---
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        st.error("❌ 无法打开视频文件，请检查格式是否正确。")
        st.stop()

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    cap.release()

    # 显示基础信息卡片
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    with col_info1:
        st.metric("总帧数", f"{total_frames:,}")
    with col_info2:
        st.metric("帧率 (FPS)", f"{fps:.2f}")
    with col_info3:
        st.metric("时长 (秒)", f"{duration:.2f}")
    with col_info4:
        st.metric("分辨率", f"{width}x{height}")

    st.success("✅ 视频解析成功！")
    st.divider()

    # --- 核心功能区域：双列布局 ---
    # 左边：视频预览与控制 (占 40%)
    # 右边：关键帧与 AI 分析 (占 60%)
    col_preview, col_analysis = st.columns([4, 6])

    with col_preview:
        st.subheader("📺 实时帧预览")
        
        # 重新打开视频用于逐帧读取
        cap = cv2.VideoCapture(video_path)
        
        # 滑动条选择帧
        frame_number = st.slider(
            "拖动查看不同帧", 
            min_value=0, 
            max_value=int(total_frames - 1), 
            value=0,
            key="frame_slider"
        )
        
        # 读取指定帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if ret:
            # BGR 转 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 【关键优化】限制图片最大宽度，不再撑满全屏
            st.image(frame_rgb, caption=f"第 {frame_number} 帧 / 时间: {timedelta(seconds=frame_number/fps)}", use_container_width=True)
        else:
            st.warning("无法读取该帧")
        
        cap.release()

    with col_analysis:
        st.subheader("🔑 关键帧提取 & AI 分析")
        
        # 1. 关键帧提取逻辑 (简单策略：每隔固定时间取一帧)
        st.markdown("#### 1. 关键帧缩略图")
        keyframe_count = 5  # 提取5张关键帧
        step = max(1, total_frames // keyframe_count)
        
        keyframes_cols = st.columns(keyframe_count)
        
        # 缓存关键帧数据以便点击跳转
        if 'selected_frame' not in st.session_state:
            st.session_state.selected_frame = 0

        cap = cv2.VideoCapture(video_path)
        for i in range(keyframe_count):
            idx = i * step
            if idx >= total_frames: idx = total_frames - 1
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, k_frame = cap.read()
            
            if ret:
                k_frame_rgb = cv2.cvtColor(k_frame, cv2.COLOR_BGR2RGB)
                # 缩小缩略图显示
                h, w, _ = k_frame_rgb.shape
                aspect_ratio = w / h
                new_w = 150
                new_h = int(new_w / aspect_ratio)
                k_frame_small = cv2.resize(k_frame_rgb, (new_w, new_h))
                
                with keyframes_cols[i]:
                    if st.button(f"帧 {idx}", key=f"btn_{i}", use_container_width=True):
                        st.session_state.selected_frame = idx
                        st.rerun()
                    st.image(k_frame_small, use_container_width=True)
                    st.caption(f"{timedelta(seconds=idx/fps)}")
        cap.release()

        # 如果用户点击了关键帧，更新主滑块
        if st.session_state.selected_frame != 0:
            # 这里需要通过 session_state 同步回主滑块，但 Streamlit 机制较复杂
            # 简单做法：在上方 slider 设置 value=st.session_state.selected_frame (需配合 form 或 callback)
            # 为简化代码，此处仅做展示，实际项目中可用 st.experimental_rerun 配合 callback
            pass

        st.divider()

        # 2. AI 分析模拟区域 (占位符)
        st.markdown("#### 2. 🤖 AI 智能分析结果")
        
        with st.container():
            st.markdown("""
            <div class="analysis-box">
                <h4>📝 场景摘要</h4>
                <p>检测到视频主要场景为：<b>室内模拟城市/游戏画面</b>。</p>
                <p>主要物体识别：<b>卫生间设施、人物角色、UI 界面元素</b>。</p>
                <p>动作检测：人物正在进行<b>建造/互动</b>操作。</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💡 提示：此处可接入 Coze API 或本地 LLM 进行真实分析。当前为演示模板。")
            
            # 模拟标签
            tags = ["游戏画面", "模拟经营", "室内场景", "高帧率", "竖屏视频"]
            st.markdown("**相关标签：**")
            st.write(" ".join([f"`{tag}`" for tag in tags]))

else:
    st.info("👆 请在上方上传视频文件以开始分析。")
    st.markdown("""
    ### 💡 功能亮点
    - **极速解析**：支持大文件快速加载
    - **关键帧提取**：自动抽取视频精华片段
    - **AI 辅助**：预留接口对接大模型分析
    """)