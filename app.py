import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import KMeans
import tempfile
import os

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

def center_crop_to_square(img):
    w, h = img.size
    short_side = min(w, h)
    left = (w - short_side) // 2
    top = (h - short_side) // 2
    right = left + short_side
    bottom = top + short_side
    return img.crop((left, top, right, bottom))

def make_palette_image(img, bg_color, origin_name):
    img = center_crop_to_square(img)
    w, h = img.size  # 现在w==h

    palette = extract_colors(img, 5)

    # 动态参数，保持相对比例
    cell_size = max(40, w // 6)
    gap = cell_size // 6
    cell_gap = cell_size // 6
    border = cell_size // 5

    # 色卡总宽度等于图片宽度
    # 色卡总宽度 = 色卡数*cell_size + (色卡数-1)*cell_gap，应等于图片宽度
    cell_gap_calc = (w - 5*cell_size) // 4 if 5*cell_size < w else cell_gap
    cell_gap = max(cell_gap_calc, 4)  # 保底4像素

    palette_total_h = cell_size
    new_w = w + 2*border
    new_h = h + gap + palette_total_h + 2*border

    new_img = Image.new('RGB', (new_w, new_h), bg_color)

    # 粘贴图片（水平居中，上方边框）
    new_img.paste(img, (border, border))

    # 画色卡（正好与图片两侧齐平）
    start_x = border
    y = border + h + gap
    draw = ImageDraw.Draw(new_img)
    for i, color in enumerate(palette):
        x = start_x + i * (cell_size + cell_gap)
        draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color)

    # 输出到临时文件
    palette_name = origin_name + "_palette.png"
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as out_tmp:
        out_path = out_tmp.name
        new_img.save(out_path)
    return out_path, palette_name

# ==== Streamlit 页面 ====
st.set_page_config(page_title="主色卡生成工具", layout="centered")
st.title("主色卡生成工具")
st.write("上传图片，将自动生成主色卡。")

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
            label="下载图片",
            data=img_bytes,
            file_name=palette_name,
            mime="image/png",
        )
    except Exception as e:
        st.error(f"生成失败：{e}")