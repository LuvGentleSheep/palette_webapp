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

def make_palette_image(img, bg_color, origin_name, num_colors=5, wide_palette=False):
    img = center_crop_to_square(img)
    w, h = img.size

    # 主色提取
    if num_colors == 5 and wide_palette:
        # “宽”模式：10色聚类，取第2/4/6/8/10色
        all_colors = extract_colors(img, 10)
        palette = [all_colors[i] for i in [0,2,4,7,9]]
    else:
        palette = extract_colors(img, num_colors)

    # 色块排列逻辑
    if num_colors == 5:
        n_per_row, n_rows = 5, 1
    elif num_colors == 8:
        n_per_row, n_rows = 4, 2
    elif num_colors == 10:
        n_per_row, n_rows = 5, 2
    else:
        raise ValueError("只支持5、8、10色")

    # 布局
    border = max(24, w // 25)
    cell_gap = max(14, w // 30)
    gap = cell_gap

    cell_size = (w - (n_per_row - 1) * cell_gap) // n_per_row

    palette_h = n_rows * cell_size + (n_rows - 1) * cell_gap
    new_w = w + 2 * border
    new_h = h + gap + palette_h + 2 * border

    new_img = Image.new('RGB', (new_w, new_h), bg_color)
    new_img.paste(img, (border, border))

    draw = ImageDraw.Draw(new_img)
    idx = 0
    for row in range(n_rows):
        n_this_row = n_per_row
        row_palette_w = n_per_row * cell_size + (n_per_row - 1) * cell_gap
        start_x = border
        y = border + h + gap + row * (cell_size + cell_gap)
        for i in range(n_this_row):
            if idx >= len(palette):
                break
            x = start_x + i * (cell_size + cell_gap)
            draw.rectangle([x, y, x + cell_size, y + cell_size], fill=palette[idx])
            idx += 1

    palette_name = origin_name + "_palette.png"
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as out_tmp:
        out_path = out_tmp.name
        new_img.save(out_path)
    return out_path, palette_name

# ==== Streamlit 页面 ====
st.set_page_config(page_title="图片色板生成工具", layout="centered")
st.title("图片色板生成工具")
st.write("上传图片，将自动生成色板。")

uploaded_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg"])

num_colors = st.radio("取色数量", options=[5, 10], index=0, horizontal=True)
#num_colors = st.radio("主色数量", options=[5, 8, 10], index=0, horizontal=True)

wide_palette = False
# 只有五色时增加宽/窄选项
if num_colors == 5:
    col1, col2 = st.columns([1,1])
    with col1:
        pick_mode = st.radio("取色范围", ["窄", "宽"], index=0, horizontal=True)
    wide_palette = (pick_mode == "宽")

color_options = {
    "白色": "#F5F5F5",
    "黑色": "#1C1C1C"
}
color_label = st.radio("选择边框色", list(color_options.keys()), index=0, horizontal=True)
bg_color = hex_to_rgb(color_options[color_label])

if uploaded_file is not None:
    try:
        origin_name = os.path.splitext(uploaded_file.name)[0]
        img = Image.open(uploaded_file)
        with st.spinner("正在生成色板，请稍候……"):
            out_path, palette_name = make_palette_image(
                img, bg_color, origin_name, num_colors=num_colors, wide_palette=wide_palette
            )
            # 图片生成期间会有加载动画
        st.image(out_path, caption="色板拼接图", use_container_width=True)
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