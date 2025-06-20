import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import KMeans
import tempfile
import os

# 1. 颜色提取与色卡生成的函数（从 make_cube_palette.py 迁移）
def extract_colors(image, num_colors=5):
    img = image.convert("RGB").resize((200, 200))
    arr = np.array(img).reshape(-1, 3)
    kmeans = KMeans(n_clusters=num_colors, random_state=42).fit(arr)
    labels = kmeans.labels_
    counts = np.bincount(labels)
    order = np.argsort(-counts)
    colors = kmeans.cluster_centers_[order].astype(int)
    return [tuple(c) for c in colors]

def hex_to_rgb(hexstr):
    hexstr = hexstr.strip().lstrip('#')
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))

def make_palette_image(img, bg_color, origin_name):
    w, h = img.size
    palette = extract_colors(img, 5)
    short_side = min(w, h)
    cell_size = max(40, short_side // 6)
    gap = cell_size // 6
    cell_gap = cell_size // 6
    border = cell_size // 5
    is_vertical = h >= w
    # 用临时文件保存图片
    with tempfile.NamedTemporaryFile(suffix='_palette.png', delete=False) as out_tmp:
        out_path = out_tmp.name
    if is_vertical:
        palette_h = 5*cell_size + 4*cell_gap
        new_w = w + gap + cell_size + 2*border
        new_h = max(h, palette_h) + 2*border
        new_img = Image.new('RGB', (new_w, new_h), bg_color)
        img_top = border + (new_h - 2*border - h) // 2
        palette_top = border + (new_h - 2*border - palette_h) // 2
        new_img.paste(img, (border, img_top))
        for i, color in enumerate(palette):
            x = border + w + gap
            y = palette_top + i * (cell_size + cell_gap)
            ImageDraw.Draw(new_img).rectangle([x, y, x+cell_size, y+cell_size], fill=color)
    else:
        palette_w = 5*cell_size + 4*cell_gap
        new_w = max(w, palette_w) + 2*border
        new_h = h + gap + cell_size + 2*border
        new_img = Image.new('RGB', (new_w, new_h), bg_color)
        img_left = border + (new_w - 2*border - w) // 2
        palette_left = border + (new_w - 2*border - palette_w) // 2
        new_img.paste(img, (img_left, border))
        for i, color in enumerate(palette):
            x = palette_left + i * (cell_size + cell_gap)
            y = border + h + gap
            ImageDraw.Draw(new_img).rectangle([x, y, x+cell_size, y+cell_size], fill=color)
    # 以“原名_palette.png”命名文件保存
    palette_name = origin_name + "_palette.png"
    new_img.save(out_path)
    return out_path, palette_name

# 2. Streamlit 网页界面
st.set_page_config(page_title="主色卡生成工具", layout="centered")
st.title("主色卡生成工具")
st.write("上传一张图片，自动生成主色卡拼接图。支持主流格式，下载按钮可直接保存分享。")

uploaded_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg"])
color_options = {
    "白色": "#F5F5F5",
    "黑色": "#1C1C1C"
}
color_label = st.radio("选择边框色", list(color_options.keys()), index=0)
bg_color = hex_to_rgb(color_options[color_label])

if uploaded_file is not None:
    try:
        origin_name = os.path.splitext(uploaded_file.name)[0]
        img = Image.open(uploaded_file)
        out_path, palette_name = make_palette_image(img, bg_color, origin_name)
        st.image(out_path, caption="主色卡拼接图", use_container_width=True)
        with open(out_path, "rb") as f:
            img_bytes = f.read()
        st.success("生成成功！可点击下方按钮下载。")
        st.download_button(
            label="下载/分享此图片",
            data=img_bytes,
            file_name=palette_name,
            mime="image/png",
        )
    except Exception as e:
        st.error(f"生成失败：{e}")