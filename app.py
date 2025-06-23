import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import numpy as np
from sklearn.cluster import KMeans
import tempfile
import os

# 1. 主色提取
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

def add_border(img, border=40, color=(245,245,245)):
    return ImageOps.expand(img, border=border, fill=color)

def pad_to_ratio(img, ratio=(16,9), color=(245,245,245)):
    w, h = img.size
    target_w = w
    target_h = int(w * ratio[1] / ratio[0])
    if target_h < h:
        target_h = h
        target_w = int(h * ratio[0] / ratio[1])
    pad_left = (target_w - w) // 2
    pad_top = (target_h - h) // 2
    padded_img = ImageOps.expand(img, border=(pad_left, pad_top, target_w - w - pad_left, target_h - h - pad_top), fill=color)
    return padded_img

def make_palette_image(img, bg_color, origin_name, num_colors=5, wide_palette=False, shape="方形"):
    img = center_crop_to_square(img)
    w, h = img.size

    # 主色提取
    if num_colors == 5 and wide_palette:
        all_colors = extract_colors(img, 10)
        palette = [all_colors[i] for i in [0,2,4,7,9]]
    else:
        palette = extract_colors(img, num_colors)
    if num_colors == 5:
        n_per_row, n_rows = 5, 1
    elif num_colors == 8:
        n_per_row, n_rows = 4, 2
    elif num_colors == 10:
        n_per_row, n_rows = 5, 2
    else:
        raise ValueError("只支持5、8、10色")
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
        start_x = border
        y = border + h + gap + row * (cell_size + cell_gap)
        for i in range(n_this_row):
            if idx >= len(palette):
                break
            x = start_x + i * (cell_size + cell_gap)
            if shape == "圆形":
                draw.ellipse([x, y, x + cell_size, y + cell_size], fill=palette[idx])
            else:
                draw.rectangle([x, y, x + cell_size, y + cell_size], fill=palette[idx])
            idx += 1
    palette_name = origin_name + "_palette.png"
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as out_tmp:
        out_path = out_tmp.name
        new_img.save(out_path)
    return out_path, palette_name, palette, new_img

# ========================== Streamlit 页面布局 ==========================
st.set_page_config(page_title="图片色板生成工具", layout="centered")
st.image("banner.jpeg", use_container_width=True)
st.title("图片色板生成工具")
st.write("上传图片，将自动生成色板。")

# 1. 上传控件单独一行
uploaded_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg"])

# 2. 参数区 和 结果区 并排 1:2
col_settings, col_result = st.columns([1, 2])

with col_settings:
    num_colors = st.radio("取色数量", options=[5, 10], index=0, horizontal=True)
    wide_palette = False
    if num_colors == 5:
        pick_mode = st.radio("取色范围", ["窄", "宽"], index=0, horizontal=True, help="只在取色数量为5时可用")
        wide_palette = (pick_mode == "宽")
    shape = st.radio("色块形状", ["方形", "圆形"], index=0, horizontal=True)
    color_options = {"白色": "#F5F5F5", "黑色": "#1C1C1C"}
    color_label = st.radio("选择边框色", list(color_options.keys()), index=0, horizontal=True)
    bg_color = hex_to_rgb(color_options[color_label])

with col_result:
    if uploaded_file is not None:
        try:
            origin_name = os.path.splitext(uploaded_file.name)[0]
            img = Image.open(uploaded_file)
            with st.spinner("正在生成色板，请稍候……"):
                out_path, palette_name, palette, palette_img = make_palette_image(
                    img, bg_color, origin_name, num_colors=num_colors,
                    wide_palette=wide_palette, shape=shape
                )
            st.image(out_path, caption="色板拼接图", use_container_width=True)
            with open(out_path, "rb") as f:
                img_bytes = f.read()
            colA, colB, colC = st.columns(3)
            with colA:
                st.download_button(
                    label="下载色板图片",
                    data=img_bytes,
                    file_name=palette_name,
                    mime="image/png",
                )
            with colB:
                if st.button("制作壁纸"):
                    st.session_state["wallpaper_start"] = True
        except Exception as e:
            st.error(f"生成失败：{e}")

# --- 壁纸生成流程 ---
if st.session_state.get("wallpaper_start"):
    st.header("制作壁纸")
    
    col_wpsettings, col_wpresult = st.columns([2, 3])
#with col_wpsettings:
# 1. 桌面/手机
    client_type = st.radio("壁纸用途", ["桌面", "手机"], horizontal=True)
    if client_type == "桌面":
        ratio = (16, 9)
    else:
        ratio = (9, 19.5)
    # 2. 色卡选择
    palette_hex = ['#%02x%02x%02x' % c for c in palette]
    n_colors = len(palette_hex)
    bar_height = 36
    
    
    # 标题
    st.markdown("<div style='font-size:1.3em;font-weight:bold;margin:8px 0 6px 0;'>选择填充色</div>", unsafe_allow_html=True)
    
    # 1. SVG色带
    rects = []
    for i, color in enumerate(palette_hex):
        w = 100 / n_colors
        x = i * w
        rects.append(f"<rect x='{x}' y='0' width='{w}' height='{bar_height}' fill='{color}'/>")
    svg_code = f"""
    <div style='width:100%;max-width:700px;margin:18px auto 10px auto;'>
    <svg width='100%' height='{bar_height}' viewBox='0 0 100 {bar_height}' style='display:block;border-radius:13px;overflow:hidden;border:2px solid #444;' preserveAspectRatio="none">
        {''.join(rects)}
    </svg>
    </div>
    """
    st.markdown(svg_code, unsafe_allow_html=True)
    
    # 2. 滑块
    if num_colors == 5:
        col_left, col_center, col_right = st.columns([1, 8, 1])
    else:  # num_colors == 10
        col_left, col_center, col_right = st.columns([1, 18, 1])
        
    with col_center:
        color_idx = st.slider(
            "",  # 无label
            min_value=1, max_value=n_colors, value=1, label_visibility="collapsed"
        ) - 1
    
    # 3. 大色块预览
    sel_color = palette[color_idx]
    preview_code = f"""
    <div style='width:100%;max-width:700px;height:48px;
        background:{palette_hex[color_idx]};
        border-radius:13px;border:3px solid #444;margin:0px auto 0 auto;'>
    </div>
    """
#   st.markdown(preview_code, unsafe_allow_html=True)
#   st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    
    if st.button("生成壁纸图片", key="wall_generate"):
        # 设置session状态，触发右侧显示
        st.session_state["wallpaper_generated"] = True
            
    # 3. 生成壁纸，边框宽度和分辨率自动（按色板图大小扩展、绝不压缩）
    palette_w, palette_h = palette_img.size
    # 根据用户选择的壁纸比例自动放大/补边
    if ratio[0] / ratio[1] > palette_w / palette_h:
        # 需要补上下
        wall_w = palette_w
        wall_h = int(palette_w * ratio[1] / ratio[0])
    else:
        # 需要补左右
        wall_h = palette_h
        wall_w = int(palette_h * ratio[0] / ratio[1])
        
    border_width = min(wall_w, wall_h) // 4
    img_to_use = palette_img
    img_to_use = add_border(img_to_use, border=border_width, color=sel_color)
    wallpaper_img = pad_to_ratio(img_to_use, ratio=ratio, color=sel_color)
    # 不再resize（保持最高质量和最初分辨率）
    
#with col_wpresult: 
    if st.session_state.get("wallpaper_generated"):
        with st.spinner("正在生成壁纸，请稍候……"):
            st.image(wallpaper_img, caption="壁纸预览", use_container_width=True)
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            wallpaper_img.save(tmp.name)
            
            # 获取原图名
            origin_name = os.path.splitext(uploaded_file.name)[0]
            # 判断横竖
            w, h = wallpaper_img.size
            orientation = "landscape" if w >= h else "portrait"
            # 拼接文件名
            wallpaper_file_name = f"{origin_name}_palette_{orientation}.png"
            
            st.download_button(
                "下载壁纸",
                data=open(tmp.name, "rb"),
                file_name=wallpaper_file_name,
                mime="image/png"
            )