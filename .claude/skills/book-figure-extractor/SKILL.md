---
name: book-figure-extractor
description: >
  从英文原版书籍PDF中精确提取插图，并嵌入对应章节的翻译Markdown文件（chapter_xxx.md）。
  当用户说"把书里的图提取出来放到翻译文件里"、"在翻译md里插入原书插图"、"提取第X章的图"、
  "书里的图没有显示"、"翻译文件缺少插图"时，必须使用此技能。
  核心能力：使用PyMuPDF定位图片真实bbox、根据caption位置估算图片区域、
  按figID+语义命名图片文件（如fig3_2-dh-frame-assignment.png）、
  将图片以正确的Markdown语法嵌入chapter_xxx.md中对应caption的位置。
  即使用户只说"把图加进去"或上传了PDF和md文件，也应立即触发此技能。
---

# 书籍插图提取与嵌入技能

## 技能概述

本技能解决以下核心问题：从英文原版书籍PDF中准确定位、裁剪插图，并将其嵌入到对应的中文翻译Markdown章节文件中，保持图片与正文的空间对应关系。

**输入**：
- 英文原版书籍 PDF（一本或单章）
- 中文翻译 `chapter_xxx.md` 文件（已翻译，含图题占位符或图题文字）

**输出**：
- 提取的图片文件，命名格式 `fig{章号}_{序号}-{语义slug}.png`，存入 `figures/` 目录
- 更新后的 `chapter_xxx.md`，在每处图题上方插入 `![...](figures/...)` 引用

---

## 工作流程

### 第一步：分析PDF结构

```bash
# 检查PDF基本信息
pdfinfo input.pdf

# 列出所有嵌入图片（含页码、尺寸）
pdfimages -list input.pdf
```

然后运行 `scripts/analyze_figures.py` 进行深度分析（见下方）。

### 第二步：运行图片定位脚本

参考 `scripts/extract_figures.py`，该脚本完成：

1. **文本扫描**：在每页用 PyMuPDF 提取所有文本块，找出 "Figure X.Y" / "Fig. X.Y" 格式的 caption
2. **bbox估算**：caption 通常紧贴图片下方（偶尔在上方），以 caption bbox 为锚点向上扩展搜索图片区域
3. **图片匹配**：用 `page.get_images()` 获取页面内嵌光栅图；对矢量图（matplotlib等）则用整页截图后按区域裁剪
4. **文件命名**：`fig{章}.{序号}-{slug}.png`，slug 由 caption 语义生成

### 第三步：语义命名规则

文件名格式：`fig{C}_{N}-{semantic-slug}.png`

| 字段 | 说明 | 示例 |
|------|------|------|
| `C` | 章节号（整数或浮点） | `3`、`10` |
| `N` | 图在本章的序号 | `2`、`12` |
| `semantic-slug` | 来自 caption 的语义摘要，英文小写连字符 | `dh-frame-assignment`、`particle-filter-localization` |

**slug 生成规则**：
- 取 caption 核心名词短语（去掉 "Figure X.Y:"、冠词、介词）
- 转为小写，空格换连字符，最多5个词
- 例：`"Figure 3.2: DH frame assignment for 2-link manipulator"` → `dh-frame-assignment`
- 例：`"Figure 4.1: Particle filter localization results"` → `particle-filter-localization`

### 第四步：嵌入到 chapter_xxx.md

在翻译 md 文件中，找到每处图题行（形如 `图 3.2：...` 或原始 caption），在其 **上方** 插入图片引用：

```markdown
![图3.2 两连杆机械臂的D-H坐标系（DH frame assignment for 2-link manipulator）](figures/fig3_2-dh-frame-assignment.png)

图 3.2：两连杆机械臂的 D-H 坐标系示意图（Figure 3.2: DH frame assignment for 2-link manipulator）
```

**对齐策略**：
- 以翻译 md 中的图题编号（`图 X.Y`）与提取的 `figC_N` 做精确匹配
- 如找不到图题，在段落末尾或章节末尾追加，并标注 `<!-- 需手动确认位置 -->`

---

## 核心脚本

### scripts/extract_figures.py

```python
"""
从书籍PDF提取插图，按figID+语义命名，输出到 figures/ 目录。
用法: python extract_figures.py <input.pdf> <chapter_num> [--pages N-M]
"""
import re
import sys
import json
from pathlib import Path
import fitz  # PyMuPDF

def slugify(text: str, max_words: int = 5) -> str:
    """将 caption 文本转为语义 slug。"""
    # 去掉 "Figure X.Y:" 前缀
    text = re.sub(r'^(Figure|Fig\.?)\s+[\d.]+[:\s]*', '', text, flags=re.IGNORECASE)
    # 只保留字母数字和空格
    text = re.sub(r'[^a-zA-Z0-9 ]', ' ', text)
    words = text.lower().split()
    # 过滤停用词
    stopwords = {'a','an','the','of','in','for','to','and','or','with','on','at','by','from'}
    words = [w for w in words if w not in stopwords and len(w) > 1]
    return '-'.join(words[:max_words])

def find_captions(page) -> list[dict]:
    """
    在页面中找到所有 "Figure X.Y" / "Fig. X.Y" caption，
    返回 [{'num': '3.2', 'text': '...', 'bbox': Rect}, ...]
    """
    captions = []
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block.get("type") != 0:  # 0 = text block
            continue
        for line in block.get("lines", []):
            line_text = " ".join(span["text"] for span in line["spans"])
            m = re.match(r'(Figure|Fig\.?)\s+([\d]+\.[\d]+)', line_text, re.IGNORECASE)
            if m:
                captions.append({
                    "num": m.group(2),           # e.g. "3.2"
                    "text": line_text.strip(),
                    "bbox": fitz.Rect(line["bbox"])
                })
    return captions

def estimate_figure_bbox(page, caption_bbox: fitz.Rect, page_height: float) -> fitz.Rect:
    """
    根据 caption bbox 估算图片区域。
    caption 通常在图片下方，图片高度约为页高的 20%~50%。
    策略：向 caption 上方扩展，取最近的非文字区域。
    """
    # 向上扩展搜索范围（从 caption 顶部向上 50% 页高）
    search_top = max(0, caption_bbox.y0 - page_height * 0.5)
    candidate = fitz.Rect(
        caption_bbox.x0 - 20,   # 左右各留20pt余量
        search_top,
        caption_bbox.x1 + 20,
        caption_bbox.y0          # 到 caption 顶部
    )
    return candidate

def extract_figures_from_pdf(pdf_path: str, chapter: int, page_range: tuple = None):
    """主提取函数。"""
    doc = fitz.open(pdf_path)
    output_dir = Path("figures")
    output_dir.mkdir(exist_ok=True)
    
    pages = range(*page_range) if page_range else range(len(doc))
    results = []  # [{fig_num, filename, page_idx, caption_text}, ...]
    
    for page_idx in pages:
        page = doc[page_idx]
        page_height = page.rect.height
        captions = find_captions(page)
        
        for cap in captions:
            fig_num = cap["num"]  # e.g. "3.2"
            chapter_num, seq_num = fig_num.split(".")
            slug = slugify(cap["text"])
            filename = f"fig{chapter_num}_{seq_num}-{slug}.png"
            out_path = output_dir / filename
            
            # 尝试提取嵌入的光栅图
            images_on_page = page.get_images(full=True)
            best_img = None
            best_overlap = 0
            
            # 估算图片区域
            fig_bbox = estimate_figure_bbox(page, cap["bbox"], page_height)
            
            for img_info in images_on_page:
                xref = img_info[0]
                # 获取图片在页面上的位置
                img_rects = page.get_image_rects(xref)
                if not img_rects:
                    continue
                img_rect = img_rects[0]
                # 计算与估算区域的重叠
                overlap = fig_bbox & img_rect
                overlap_area = overlap.get_area() if overlap else 0
                if overlap_area > best_overlap:
                    best_overlap = overlap_area
                    best_img = xref
            
            if best_img and best_overlap > 100:
                # 提取嵌入光栅图
                pix = fitz.Pixmap(doc, best_img)
                if pix.n - pix.alpha > 3:  # CMYK → RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                pix.save(str(out_path))
            else:
                # 矢量图或未找到：裁剪页面渲染
                mat = fitz.Matrix(2.0, 2.0)  # 2x 分辨率
                clip = fig_bbox
                pix = page.get_pixmap(matrix=mat, clip=clip)
                pix.save(str(out_path))
            
            results.append({
                "fig_num": fig_num,
                "chapter": int(chapter_num),
                "seq": int(seq_num),
                "filename": filename,
                "page": page_idx + 1,
                "caption": cap["text"],
                "slug": slug
            })
            print(f"  ✓ 提取 Figure {fig_num} → {filename}  (page {page_idx+1})")
    
    doc.close()
    # 保存索引
    with open("figures/index.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results

if __name__ == "__main__":
    pdf_path = sys.argv[1]
    chapter = int(sys.argv[2])
    results = extract_figures_from_pdf(pdf_path, chapter)
    print(f"\n共提取 {len(results)} 张图片，索引保存至 figures/index.json")
```

### scripts/inject_figures.py

```python
"""
将提取的图片嵌入到 chapter_xxx.md 文件中。
用法: python inject_figures.py <chapter_xxx.md> <figures/index.json>
"""
import re
import json
import sys
from pathlib import Path

def inject_figures(md_path: str, index_path: str):
    md_file = Path(md_path)
    text = md_file.read_text(encoding="utf-8")
    lines = text.split("\n")
    
    with open(index_path, encoding="utf-8") as f:
        figures = json.load(f)
    
    # 建立 fig_num → filename 映射
    fig_map = {fig["fig_num"]: fig for fig in figures}
    
    new_lines = []
    injected = set()
    
    for line in lines:
        # 匹配中文图题：图 3.2：... 或 Figure 3.2: ...
        m = re.search(r'(?:图|Figure|Fig\.?)\s*([\d]+\.[\d]+)', line)
        if m:
            fig_num = m.group(1)
            if fig_num in fig_map and fig_num not in injected:
                fig = fig_map[fig_num]
                img_path = f"figures/{fig['filename']}"
                alt_text = f"图{fig_num} {fig['slug'].replace('-', ' ')}"
                # 在图题行上方插入图片
                new_lines.append(f"![{alt_text}]({img_path})")
                new_lines.append("")  # 空行
                injected.add(fig_num)
        new_lines.append(line)
    
    # 报告未找到位置的图
    missing = set(fig_map.keys()) - injected
    if missing:
        new_lines.append("\n\n<!-- 以下图片未找到对应图题位置，请手动放置 -->")
        for fig_num in sorted(missing):
            fig = fig_map[fig_num]
            new_lines.append(f"<!-- Figure {fig_num}: ![图{fig_num}](figures/{fig['filename']}) -->")
    
    # 写回
    output = "\n".join(new_lines)
    md_file.write_text(output, encoding="utf-8")
    print(f"✓ 已注入 {len(injected)} 张图片到 {md_path}")
    if missing:
        print(f"⚠ {len(missing)} 张图片未匹配到图题位置：{missing}")

if __name__ == "__main__":
    inject_figures(sys.argv[1], sys.argv[2])
```

---

## 完整工作流（提取 → 验证 → 自动重试）

```bash
# 1. 安装依赖（如未安装）
pip install PyMuPDF --break-system-packages

# 2. 首次提取图片（指定章节号，可选页范围）
python scripts/extract_figures.py book.pdf 3

# 3. Claude AI视觉验证提取质量
# 3.1 生成验证任务，Claude 直接使用 Read 工具读取每张图片进行验证
python scripts/verify_extraction.py figures/verification_tasks.json

# 4. 自动重试验证失败的图片（脚本会分析失败原因自动调整参数重试）
python scripts/extract_figures.py book.pdf 3 --retry-failed

# 5. 重复步骤 3 → 验证新提取的结果，直到全部通过

# 6. 所有图片验证通过后，嵌入到翻译文件
python scripts/inject_figures.py chapter_003.md figures/index.json

# 7. 检查结果
ls figures/                          # 图片文件
cat figures/index.json              # 提取索引
cat figures/verification_tasks.json  # 验证结果
```

---

## 自动重试机制

验证失败后，使用 `--retry-failed` 参数运行，脚本会：

1. **自动分析失败原因**：
   - 如果失败原因是**图片裁切不全/不完整** → **增大向上搜索范围**（+15% page height）
   - 如果失败原因是**包含多余文字/正文** → **加宽x方向边距**（+20pt）

2. **只重新提取失败图片** → 不会动已经验证通过的图片

3. **重置验证状态** → 需要重新验证新提取的图片

## AI视觉验证流程

提取完成后必须进行两项验证，由Claude AI视觉能力执行：

### 验证步骤

Claude Code agent 原生支持直接读取本地图片文件进行视觉分析，验证流程自动进行：

1. **完整性验证**：
   - ✅ 通过：图片只包含完整图形，不包含多余文字/背景，完整显示无截断
   - ❌ 失败：图片裁切不全，包含多余文字，或多个图混在一起

2. **Caption匹配验证**：
   - ✅ 通过：图片内容与caption文字描述一致
   - ❌ 失败：提取了错误的图片，内容与caption不匹配

验证由 agent 自动执行：脚本生成 `verification_tasks.json` 后，agent 使用 Read 工具依次读取每张图片，直接进行视觉分析并将结果写回文件。

### 验证输出

验证结果保存在 `figures/verification_tasks.json`，包含每个图的验证状态、结果和注释。验证失败的图片需要重新提取或手动调整裁剪区域。

---

## 边缘情况处理

### 跨页图片

有时一张大图跨越两页。解决方案：
- 检查 caption 所在页 **前一页** 的底部是否有图片内容
- 若是，截图两页底部+顶部拼接

### 双栏版式

学术书籍常见双栏。策略：
- 检测页面宽度中线，将 caption bbox 的 x 坐标判断属于左栏或右栏
- 将 `estimate_figure_bbox` 的 x 范围限制在对应栏内

### 多图共享 caption 区域

例如 `(a)` `(b)` 子图。策略：
- 检测 caption 中含 `(a)` / `(b)` 的情况
- 提取整个组合图区域，不拆分
- 文件名加 `-composite` 后缀

### 纯矢量图（无嵌入光栅图）

- 直接渲染整页后按估算 bbox 裁剪（见 `extract_figures.py` 的 fallback 路径）
- 分辨率建议 2x（`fitz.Matrix(2.0, 2.0)`）保证清晰度

---

## 输出目录结构

```
chapter_003.md          ← 已注入图片引用的翻译文件
figures/
├── index.json              ← 提取索引（fig_num, filename, page, caption）
├── verification_tasks.json ← 验证任务与结果（完整性+caption匹配）
├── fig3_1-manipulator-dof.png
├── fig3_2-dh-frame-assignment.png
├── fig3_3-homogeneous-transform.png
└── ...
```

---

## 依赖

- `PyMuPDF` (`fitz`) — PDF解析、图片提取、页面渲染
- Python 标准库：`re`, `json`, `pathlib`, `argparse`
- 验证：Claude Code 视觉能力（用于完整性和匹配检查）
- 可选：`pdfimages`（poppler-utils，用于预检）

安装：
```bash
pip install PyMuPDF --break-system-packages
```

- `PyMuPDF` (`fitz`) — PDF解析、图片提取、页面渲染
- Python 标准库：`re`, `json`, `pathlib`
- 可选：`pdfimages`（poppler-utils，用于预检）

安装：
```bash
pip install PyMuPDF --break-system-packages
```
