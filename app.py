import os
import streamlit as st
from PIL import Image
import tempfile
import subprocess
import shutil

st.set_page_config(page_title="主色卡生成工具", layout="centered")

st.title("主色卡生成工具")
st.write("上传一张图片，自动生成主色卡拼接图")


uploaded_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg"])

color_options = {
    "白色": "#F5F5F5",
    "黑色": "#1C1C1C"
}
color_label = st.radio("选择边框色", list(color_options.keys()), index=0)
bg_color = color_options[color_label] 

if uploaded_file is not None:
    origin_name = os.path.splitext(uploaded_file.name)[0]  # 去掉扩展名
    palette_name = origin_name + "_palette.png"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
        temp_img.write(uploaded_file.read())
        temp_img_path = temp_img.name

    cmd = [
        "python3", "make_cube_palette.py",
        temp_img_path,
        bg_color
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output_path = result.stdout.strip().split("\n")[-1]
        out_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        shutil.copy(output_path, out_tmp.name)
        st.image(out_tmp.name, caption="主色卡拼接图", use_container_width=True)
        # ---- 这里是分享/下载按钮 ----
        with open(out_tmp.name, "rb") as f:
            img_bytes = f.read()
        st.success("生成成功！可点击下方按钮下载。")
        st.download_button(
            label="下载此图片",
            data=img_bytes,
            file_name=palette_name,
            mime="image/png",
        )
    except Exception as e:
        st.error(f"生成失败：{e}")