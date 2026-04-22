# 图片定位与 Caption 检测参考手册

## Caption 在页面中的典型位置

### 最常见：caption 在图片正下方

```
┌─────────────────────────────────┐
│  [正文文字区域]                  │
│                                  │
│  ┌───────────────────────────┐   │
│  │                           │   │
│  │         图片内容           │   │  ← 光栅/矢量图区域
│  │                           │   │
│  └───────────────────────────┘   │
│  Figure 3.2: Caption 文字...      │  ← caption bbox
│                                  │
│  [继续正文]                       │
└─────────────────────────────────┘
```

**处理策略**：从 caption.y0 向上搜索，估算图片在 caption 上方约 20%~55% 页高范围内。

---

### 较少见：caption 在图片上方

```
│  Figure 3.2: Caption 文字...      │  ← caption bbox
│  ┌───────────────────────────┐   │
│  │         图片内容           │   │
│  └───────────────────────────┘   │
```

**处理策略**：若向上搜索无内容，改向 caption.y1 向下搜索。脚本默认优先向上搜索，可调 `search_above` 参数。

---

### 双栏版式（学术书籍常见）

```
┌─────────────┬──────────────┐
│  正文（左栏）│  正文（右栏）  │
│             │              │
│  ┌────────┐ │              │
│  │ 图片   │ │              │
│  └────────┘ │              │
│  Fig 3.2: ..│              │
└─────────────┴──────────────┘
```

**处理策略**：
- 检测 caption 的 x 中心点相对页面中线的位置
- 将 `estimate_figure_bbox` 的 x 范围限制在对应栏（左：0~page_width/2，右：page_width/2~page_width）

```python
page_midx = page_rect.width / 2
if caption_bbox.x0 + caption_bbox.width/2 < page_midx:
    # 左栏
    x0, x1 = 0, page_midx
else:
    # 右栏
    x0, x1 = page_midx, page_rect.width
```

---

### 跨页图片

图片在第 N 页底部，caption 在第 N+1 页顶部。

**检测方法**：
```python
# 在 page N+1 找到 caption 后，若 estimate_figure_bbox 的区域几乎为空（caption 在页面顶部）
if caption_bbox.y0 < page_rect.height * 0.15:
    # 可能是跨页图，检查前一页底部
    prev_page = doc[page_idx - 1]
    prev_region = fitz.Rect(0, prev_page.rect.height * 0.5, prev_page.rect.width, prev_page.rect.height)
    render_page_region(prev_page, prev_region, out_path)
```

---

### 复合子图 (a)(b)(c)

```
┌────────────┬────────────┐
│            │            │
│   (a) 图a  │   (b) 图b  │
│            │            │
└────────────┴────────────┘
Figure 3.5: (a) Left view (b) Right view
```

**检测方法**：caption 包含 "(a)" 或 "(b)" 字样。

**处理策略**：提取整个复合区域为一张图，不拆分子图。文件名加 `-composite`：
```
fig3_5-composite-left-right-view.png
```

---

## 常见的 Caption 格式变体

| 格式 | 示例 |
|------|------|
| 标准 | `Figure 3.2: Description text` |
| 缩写 | `Fig. 3.2: Description text` |
| 无冒号 | `Figure 3.2 Description text` |
| 全大写 | `FIGURE 3.2: DESCRIPTION` |
| 续行 | `Figure 3.2: Long description that` + `wraps to the next line` |
| 带子图 | `Figure 3.2: (a) First view, (b) Second view` |
| 算法书常见 | `Figure 3.2 (Source: Smith 2019)` |

正则覆盖：
```python
r'(Figure|Fig\.?)\s+([\d]+\.[\d]+)\s*[:\s]'
```

---

## pdfimages 输出解读

```
page   num  type   width height color comp bpc  enc interp  object ID x-ppi y-ppi size ratio
-----  ---  -----  ----- ------ ----- ---- ---  --- ------  --------- ----- ----- ---- -----
    3    0  image   1234    890  rgb     3   8  jpeg   no       12   0   150   150 320K  31%
    3    1  mask     200    150  gray    1   1  ccitt  no       13   0   150   150  12K  53%
    5    2  image    800    600  rgb     3   8  image  no       22   0   200   200 420K  29%
```

- `type=image`：真实内容图
- `type=mask`：蒙版/背景，通常可忽略
- `width×height < 100×100`：可能是图标/装饰，过滤
- `bpc=1` + `gray`：通常是线条图/扫描黑白图

---

## PyMuPDF 坐标系

- 原点在**左上角**
- y 轴向下增大
- 单位：pt（点，1 pt = 1/72 英寸）
- A4 页面：595 × 842 pt
- 标准学术书页面（6×9 英寸）：432 × 648 pt

`fitz.Rect(x0, y0, x1, y1)` 其中 (x0,y0) 为左上，(x1,y1) 为右下。

---

## 图片质量参数建议

| 用途 | dpi_scale | 说明 |
|------|-----------|------|
| 快速预览 | 1.0 | 低分辨率，文件小 |
| 标准输出 | 2.0 | 推荐默认，清晰度好 |
| 印刷级 | 3.0 | 文件较大，适合高清需求 |

---

## 故障排查

### 问题：提取的图片是空白
- 可能原因：图片是矢量图，`pdfimages` 无法列出
- 解决：使用渲染裁剪模式（`render_page_region`）

### 问题：图片裁剪范围错误（裁到文字）
- 可能原因：caption 在图片上方，或图片与 caption 之间距离过大
- 解决：调大 `search_above` 参数，或手动指定页面范围

### 问题：找到多余小图（图标、Logo）
- 可能原因：`best_overlap` 阈值过低
- 解决：将 `overlap > 500` 调高到 `1000`+，或按图片面积过滤（宽>100, 高>100）

### 问题：caption 检测遗漏
- 可能原因：PDF 是扫描版，文字为图片而非可选文本
- 解决：先 OCR，再运行提取（参见 `pdf-reading/SKILL.md` 的 OCR 部分）
