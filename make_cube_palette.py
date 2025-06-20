import sys
import os
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import KMeans

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

def make_palette_image(img_path, bg_color):
    img = Image.open(img_path)
    img = center_crop_to_square(img)
    w, h = img.size  # 现在w==h

    palette = extract_colors(img, 5)

    # 动态参数，依然保持相对比例
    cell_size = max(40, w // 6)
    gap = cell_size // 6
    cell_gap = cell_size // 6
    border = cell_size // 5

    # 色卡总宽度等于图片宽度
    palette_total_w = w
    palette_total_h = cell_size

    # 色卡总宽度 = 色卡数*cell_size + (色卡数-1)*cell_gap，应等于图片宽度
    # 调整cell_size和cell_gap使得两侧正好齐平
    cell_gap = (w - 5*cell_size) // 4 if 5*cell_size < w else cell_gap
    if cell_gap < 4: cell_gap = 4  # 保底

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

    # 输出
    dir_name, base_name = os.path.split(img_path)
    name, ext = os.path.splitext(base_name)
    out_path = os.path.join(dir_name, f"{name}_palette.png")
    new_img.save(out_path)
    print(out_path)

if __name__ == '__main__':
    img_path = sys.argv[1]
    bg_hex = sys.argv[2] if len(sys.argv) > 2 else "#F5F5F5"
    bg_color = hex_to_rgb(bg_hex)
    make_palette_image(img_path, bg_color)