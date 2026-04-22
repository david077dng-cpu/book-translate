"""
从书籍PDF提取插图，按figID+语义命名，输出到 figures/ 目录。

用法:
    python extract_figures.py <input.pdf> <chapter_num> [--pages START-END] [--retry-failed]

示例:
    python extract_figures.py robotics_ch3.pdf 3                      # 首次提取
    python extract_figures.py full_book.pdf 3 --retry-failed    # 只重提验证失败的图

验证说明:
    提取完成后会自动生成验证任务文件 `figures/verification_tasks.json`
    使用 Claude Code 视觉能力运行验证：
    1. 图完整性验证：检查图是否完整，不包含多余部分
    2. Caption匹配验证：检查图像内容与caption描述一致
    验证后重新运行并加 --retry-failed 选项可自动只重新提取失败的图片
    脚本会自动根据失败原因分析调整参数后重试
"""
import re
import sys
import json
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("请先安装 PyMuPDF: pip install PyMuPDF --break-system-packages")
    sys.exit(1)


# ── 停用词（slug 生成时过滤）──────────────────────────────────────────────
STOPWORDS = {
    'a','an','the','of','in','for','to','and','or','with','on','at',
    'by','from','its','this','that','is','are','be','as','using','based'
}


def slugify(text: str, max_words: int = 5) -> str:
    """将 caption 文本转为语义 slug。

    示例:
        "Figure 3.2: DH frame assignment for 2-link manipulator"
        → "dh-frame-assignment"
    """
    # 去掉 "Figure X.Y:" / "Fig. X.Y:" 前缀
    text = re.sub(r'^(Figure|Fig\.?)\s+[\d.]+[:\s]*', '', text, flags=re.IGNORECASE)
    # 去掉括号内容
    text = re.sub(r'\(.*?\)', ' ', text)
    # 只保留字母数字
    text = re.sub(r'[^a-zA-Z0-9 ]', ' ', text)
    words = text.lower().split()
    words = [w for w in words if w not in STOPWORDS and len(w) > 1]
    slug = '-'.join(words[:max_words])
    return slug or 'figure'


def find_captions(page) -> list:
    """
    在页面中找到所有 "Figure X.Y" / "Fig. X.Y" caption。
    返回列表：[{'num': '3.2', 'text': '...full caption...', 'bbox': Rect}]
    """
    captions = []

    # 提取页面所有文字块（含位置）
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

    # 将文字块按 y 坐标排序（从上到下）
    text_blocks = [b for b in blocks if b.get("type") == 0]
    text_blocks.sort(key=lambda b: b["bbox"][1])

    i = 0
    while i < len(text_blocks):
        block = text_blocks[i]
        block_text = ""
        for line in block.get("lines", []):
            line_text = " ".join(span["text"] for span in line["spans"])
            block_text += " " + line_text
        block_text = block_text.strip()

        # 检测是否以 Figure/Fig 开头
        m = re.match(r'(Figure|Fig\.?)\s+([\d]+\.[\d]+)', block_text, re.IGNORECASE)
        if m:
            fig_num = m.group(2)

            # 尝试合并跨行的 caption（检查下一个 block 是否是续行）
            full_caption = block_text
            bbox = fitz.Rect(block["bbox"])

            # 有些 caption 跨多个文字块（换行），最多往下看2块
            j = i + 1
            while j < min(i + 3, len(text_blocks)):
                next_block = text_blocks[j]
                next_text = " ".join(
                    " ".join(span["text"] for span in line["spans"])
                    for line in next_block.get("lines", [])
                ).strip()
                # 下一块如果也是 Figure 开头，停止合并
                if re.match(r'(Figure|Fig\.?)\s+[\d]+\.[\d]+', next_text, re.IGNORECASE):
                    break
                # 如果下一块 y 坐标紧接（小于 25pt 间距），则合并
                gap = next_block["bbox"][1] - block["bbox"][3]
                if 0 <= gap <= 25:
                    full_caption += " " + next_text
                    bbox = bbox | fitz.Rect(next_block["bbox"])
                    j += 1
                else:
                    break

            captions.append({
                "num": fig_num,
                "text": full_caption,
                "bbox": bbox
            })
        i += 1

    return captions


def estimate_figure_bbox(
    page,
    caption_bbox: fitz.Rect,
    page_rect: fitz.Rect,
    search_above: float = 0.55,
    margin_x: int = 30
) -> fitz.Rect:
    """
    根据 caption bbox 估算图片所在区域。

    策略：
    - **绝大多数图书排版：图片在上，caption在下** → 默认向 caption 上方扩展
    - 少数例外：只有 caption 非常接近页面顶部（<15% 页高）才认为 caption 在图片上方 → 向下扩展
    - **双栏检测**：如果 caption 明显在左半或右半，x范围限制在栏内，避免跨栏提取到另一栏文字

    返回裁剪区域 Rect。
    """
    page_height = page_rect.height
    page_width = page_rect.width
    mid_page = page_width * 0.45  # 双栏中线偏左

    # 双栏排版检测：判断 caption 属于左栏还是右栏
    # 如果整个 caption bbox 在中线左边 → 左栏
    # 如果整个 caption bbox 在中线右边 → 右栏
    # 如果跨中线 → 不限制，用完整宽度
    if caption_bbox.x1 < mid_page:
        # 整个 caption 在左栏，x 最大不超过中线
        x0 = max(0, caption_bbox.x0 - margin_x)
        x1 = min(page_width * 0.5, caption_bbox.x1 + margin_x)
    elif caption_bbox.x0 > mid_page:
        # 整个 caption 在右栏，x 最小从中线开始
        x0 = max(page_width * 0.4, caption_bbox.x0 - margin_x)
        x1 = min(page_width, caption_bbox.x1 + margin_x)
    else:
        # caption 跨中线，不限制宽度
        x0 = max(0, caption_bbox.x0 - margin_x)
        x1 = min(page_width, caption_bbox.x1 + margin_x)

    # 只有 caption 非常接近页面顶部，才认为 caption 在图片上方，向下搜索
    # 绝大多数情况都是图片在上，caption在下，所以默认向上搜索
    if caption_bbox.y0 < page_height * 0.15:
        #  caption 在图片上方，图片在 caption 下方，向下扩展
        search_bottom = min(page_height, caption_bbox.y1 + page_height * search_above)
        # 最终区域：从 caption 底部到搜索底部
        fig_region = fitz.Rect(x0, caption_bbox.y1, x1, search_bottom)
    else:
        # 默认情况：caption 在图片下方，图片在 caption 上方，向上扩展
        search_top = max(0, caption_bbox.y0 - page_height * search_above)
        # 最终区域：从搜索顶部到 caption 顶部
        fig_region = fitz.Rect(x0, search_top, x1, caption_bbox.y0)

    return fig_region


def find_best_raster_image(page, doc, fig_region: fitz.Rect):
    """
    在 fig_region 内寻找最匹配的嵌入光栅图。
    返回 (xref, overlap_area)，未找到时返回 (None, 0)。
    过滤掉明显太小的图片，这些通常是水印/装饰，不是真正的插图。
    """
    best_xref = None
    best_overlap = 0
    page_width = page.rect.width

    for img_info in page.get_images(full=True):
        xref = img_info[0]

        # 获取该图片在页面上的所有位置
        try:
            img_rects = page.get_image_rects(xref)
        except Exception:
            continue

        if not img_rects:
            continue

        for img_rect in img_rects:
            # 过滤极小图片（图标、装饰等）
            if img_rect.width < 30 or img_rect.height < 30:
                continue

            # 如果图片宽度明显小于页面宽度的 1/4，很可能是水印/小装饰，不是真正的插图
            if img_rect.width < page_width * 0.25:
                continue

            intersection = fig_region & img_rect
            if intersection.is_empty:
                continue

            overlap = intersection.get_area()
            # 倾向于选面积更大的图
            score = overlap * (img_rect.get_area() ** 0.3)

            if score > best_overlap:
                best_overlap = overlap
                best_xref = xref

    return best_xref, best_overlap


def extract_image_by_xref(doc, xref, out_path: Path):
    """提取嵌入的光栅图并保存。"""
    pix = fitz.Pixmap(doc, xref)
    # CMYK 或其他非 RGB 空间 → 转 RGB
    if pix.n - pix.alpha > 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    pix.save(str(out_path))
    pix = None  # 释放内存


def render_page_region(page, region: fitz.Rect, out_path: Path, dpi_scale: float = 2.0):
    """渲染页面指定区域（用于矢量图 fallback）。"""
    mat = fitz.Matrix(dpi_scale, dpi_scale)
    clip = region
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
    pix.save(str(out_path))
    pix = None


def extract_figures_from_pdf(
    pdf_path: str,
    chapter: int,
    page_range: tuple = None,
    output_dir: str = "figures",
    dpi_scale: float = 2.0,
    verbose: bool = True,
    retry_failed: bool = False
) -> list:
    """
    主提取函数。

    Args:
        pdf_path:    PDF 文件路径
        chapter:     章节编号（用于验证 fig_num 是否属于本章）
        page_range:  (start, end) 0-based 页面范围，None 表示全文
        output_dir:  图片输出目录
        dpi_scale:   矢量图渲染倍率（2.0 = 2x 分辨率）
        verbose:     是否打印进度
        retry_failed: 是否只重新提取验证失败的图片

    Returns:
        提取结果列表，每项含 fig_num, filename, page, caption, slug
    """
    doc = fitz.open(pdf_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 如果是重试模式，读取已有验证结果，只提取失败的图片
    retry_tasks = []
    verify_path = out_dir / "verification_tasks.json"
    if retry_failed and verify_path.exists():
        with open(verify_path, "r", encoding="utf-8") as f:
            existing_verification = json.load(f)
        # 收集所有验证失败的任务需要重试
        for task in existing_verification:
            v = task["verification"]
            # 需要重试的情况：
            # 1. 验证结果为 False（已经验证过但失败）
            # 2. 结果为 None（还未验证，需要重新提取后验证）
            i_result = v["integrity"]["result"]
            m_result = v["caption_match"]["result"]
            if i_result is False or m_result is False or i_result is None or m_result is None:
                retry_tasks.append(task)
        if not retry_tasks:
            if verbose:
                print("✅ 没有需要重试的图片，所有图片都验证通过")
            doc.close()
            return []
        if verbose:
            print(f"🔄 重试模式：需要重新提取 {len(retry_tasks)} 张验证失败的图片")

    total_pages = len(doc)
    if page_range:
        start, end = page_range
        pages = range(max(0, start), min(total_pages, end + 1))
    else:
        pages = range(total_pages)

    results = []
    seen_figs = set()  # 防止同一图被重复提取（有时 caption 跨页）

    # 如果是重试模式，直接按重试任务提取，不需要全页扫描
    if retry_tasks:
        for task in retry_tasks:
            fig_num = task["fig_num"]
            # 获取保存在任务中的参数，根据失败原因调整
            params = task.get("parameters", {"search_above": 0.55, "margin_x": 30})
            search_above = params["search_above"]
            margin_x = params["margin_x"]

            # 分析失败原因，调整参数
            v = task["verification"]
            i_comment = v["integrity"].get("comment", "")

            # 如果失败原因是图片被裁切（下半截/不完整），说明搜索范围不够，需要向上扩展更多
            if i_comment and ("截断" in i_comment or "裁切" in i_comment or "不完整" in i_comment):
                search_above = min(search_above + 0.15, 0.85)
                if verbose:
                    print(f"    ⚙ Figure {fig_num}: 检测到裁切失败，增大搜索范围: {search_above:.2f}")

            # 如果失败原因是包含多余文字/左侧有正文，说明x方向需要加宽
            if i_comment and ("多余文字" in i_comment or "正文" in i_comment):
                margin_x = min(margin_x + 20, 60)
                if verbose:
                    print(f"    ⚙ Figure {fig_num}: 检测到多余文字，加宽边距: {margin_x}pt")

            # 获取页码和caption bbox（从任务中恢复）
            # 🚨 重要：在重新提取之前必须验证页码是否正确！
            # 即使任务中保存了页码，也要全页搜索确认caption位置，避免在错误页码提取
            found_page = None
            found_cap = None

            # 首先全页搜索确认caption的真实位置
            # p.number 是 0-based 页码（PyMuPDF 迭代从0开始）
            # task["page"] 是 1-based 页码（用户可见记法）
            found_page_0 = None
            found_cap = None
            for p in doc:
                captions_all = find_captions(p)
                for cap in captions_all:
                    if cap["num"] == fig_num:
                        found_page_0 = p.number  # 0-based
                        found_cap = cap
                        break
                if found_cap is not None:
                    break

            if found_cap is None:
                if verbose:
                    print(f"    ❌ Figure {fig_num}: 在PDF中找不到此caption，跳过")
                continue

            # 检查记录的页码是否与实际位置一致
            # task["page"] 是 1-based，found_page_0 是 0-based → 转换比较
            if "page" in task and (found_page_0 + 1) != task["page"]:
                if verbose:
                    print(f"    🔍 Figure {fig_num}: 页码已更正 {task['page']} → {found_page_0 + 1}")
            page_idx = found_page_0  # already 0-based
            page = doc[page_idx]
            cap_bbox = found_cap["bbox"]

            page_rect = page.rect

            # 生成文件名
            slug = slugify(task["caption"])
            cap_parts = fig_num.split(".")
            if len(cap_parts) != 2:
                continue
            cap_chapter, seq_num = cap_parts
            filename = f"fig{cap_chapter}_{seq_num}-{slug}.png"
            out_path = out_dir / filename

            # 判断是否需要跨页：
            # 排版规则：图片永远在上，caption 永远在下
            # 情况 1：caption 在当前页顶部 → 图片的一部分在前一页底部 → 需要跨页拼接（图片在上，caption 在下）
            # 情况 2：caption 在当前页下部，caption 上方剩余空间不足放下整张图 → 图片一部分在前一页底部
            # 情况 3：caption 在栏底部（y0 > 70% 页高）→ 即使空间看起来够，文字已经占满，图片可能一部分在前一页底部
            cross_page = False
            required_height = page_rect.height * search_above
            available_space = cap_bbox.y0  # 从页顶到 caption 顶部的空间

            # 双栏排版检测：判断 caption 属于左栏还是右栏
            # 如果整个 caption bbox 在中线左边 → 左栏
            # 如果整个 caption bbox 在中线右边 → 右栏
            # 如果跨中线 → 不限制，用完整宽度
            page_width = page_rect.width
            mid_page = page_width * 0.5
            x0_same = None
            x1_same = None
            x0_other = None
            x1_other = None
            if cap_bbox.x1 < mid_page:
                # 整个 caption 在左栏，x 最大不超过中线 → 同栏提取
                x0_same = max(0, cap_bbox.x0 - margin_x)
                x1_same = min(mid_page, cap_bbox.x1 + margin_x)
                # 尝试另一栏：caption在左栏，图片可能在当前页右栏（因为caption已经到页底了）
                x0_other = mid_page
                x1_other = page_width  # 右栏从mid到页面最右
            elif cap_bbox.x0 > mid_page:
                # 整个 caption 在右栏，x 最小从中线开始 → 同栏提取
                x0_same = max(mid_page, cap_bbox.x0 - margin_x)
                x1_same = min(page_width, cap_bbox.x1 + margin_x)
                # 尝试另一栏：caption在右栏，图片可能在当前页左栏（因为caption已经到页底了）
                x0_other = 0  # 左栏从页面最左到mid
                x1_other = mid_page
            else:
                # caption 跨中线，不限制宽度，不需要尝试另一栏
                x0_same = max(0, cap_bbox.x0 - margin_x)
                x1_same = min(page_width, cap_bbox.x1 + margin_x)
                x0_other = None
                x1_other = None

            # 特殊情况：双栏排版，caption 在某一栏，而且 caption 非常靠下 (> 70% 页高)
            # → 这一栏已经快结束了，整个图片肯定在同一页另一栏，不需要跨页！直接提取
            if cap_bbox.y0 > page_rect.height * 0.7 and x0_other is not None:
                # caption 在某一栏底部，整个图片在同一页另一栏
                if verbose:
                    print(f"    🔍 Figure {fig_num}: Caption接近栏尾，图片完整在同一页另一栏，直接提取")
                # 提取当前页另一栏，从顶到 caption 顶部
                other_region = fitz.Rect(x0_other, 0, x1_other, cap_bbox.y0)
                other_pix = page.get_pixmap(matrix=mat, clip=other_region, alpha=False)
                samples_other = other_pix.samples
                non_white_count_other = sum(1 for pixel in samples_other if pixel < 255)
                if non_white_count_other >= max(5, len(samples_other) * 0.0001):
                    # 找到图片了，直接保存
                    other_pix.save(str(out_path))
                    extracted_via = "same-page-other-col-direct"
                    results.append({
                        "fig_num": fig_num,
                        "chapter": int(cap_chapter),
                        "seq": int(seq_num),
                        "filename": filename,
                        "page": page_idx + 1,
                        "caption": task["caption"],
                        "slug": slug,
                        "via": extracted_via,
                        "parameters": {"search_above": search_above, "margin_x": margin_x}
                    })
                    if verbose:
                        icon = "📷" if extracted_via == "raster" else "🖼 "
                        print(f"    {icon} Figure {fig_num} → {filename}  (p.{page_idx+1}, {extracted_via})")
                    continue  # 下一个图
                # same-page other-col is blank: image isn't here, must be on previous page other column
                elif page_idx > 0:
                    if verbose:
                        print(f"    🔍 Figure {fig_num}: 当前页另一栏全空白，尝试提取前一页另一栏")
                    prev_page = doc[page_idx - 1]
                    prev_rect = prev_page.rect
                    # extract entire other column from previous page
                    prev_other_region = fitz.Rect(x0_other, 0, x1_other, prev_rect.height)
                    prev_other_pix = prev_page.get_pixmap(matrix=mat, clip=prev_other_region, alpha=False)
                    samples_prev = prev_other_pix.samples
                    non_white_count_prev = sum(1 for pixel in samples_prev if pixel < 255)
                    if non_white_count_prev >= max(5, len(samples_prev) * 0.0001):
                        # found image on previous page other column
                        prev_other_pix.save(str(out_path))
                        extracted_via = "prev-page-other-col"
                        results.append({
                            "fig_num": fig_num,
                            "chapter": int(cap_chapter),
                            "seq": int(seq_num),
                            "filename": filename,
                            "page": page_idx + 1,
                            "caption": task["caption"],
                            "slug": slug,
                            "via": extracted_via,
                            "parameters": {"search_above": search_above, "margin_x": margin_x}
                        })
                        if verbose:
                            icon = "📷" if extracted_via == "raster" else "🖼 "
                            print(f"    {icon} Figure {fig_num} → {filename}  (p.{page_idx+1}, {extracted_via})")
                        continue
                # still blank: fall through to normal cross-page detection

            if cap_bbox.y0 < page_rect.height * 0.15:
                # 情况 1: caption 在页顶
                if page_idx > 0:
                    cross_page = True
                    if verbose:
                        print(f"    📄 Figure {fig_num}: Caption在页顶，检测到跨页，拼接前一页底部")
            elif (available_space < required_height * 0.8) or (cap_bbox.y0 > page_rect.height * 0.7 and page_idx > 0):
                # 情况 2/3:
                # - 可用空间不足需要的 80%
                # - 或者 caption 非常靠下（> 70%），即使空间够，文字占满了，图片需要跨页
                if page_idx > 0:
                    cross_page = True
                    if available_space < required_height * 0.8:
                        print(f"    📄 Figure {fig_num}: 图片空间不足，检测到跨页，拼接前一页底部")
                    else:
                        print(f"    📄 Figure {fig_num}: Caption接近栏底，检测到跨页，拼接前一页底部")

            extracted_via = None
            if cross_page:
                # 向上跨页拼接：前一页底部 + 当前页顶部
                # caption 在当前页，图片从 caption 向上延伸，一部分进入前一页底部
                required_height = int(page_rect.height * search_above)
                available_on_curr = cap_bbox.y0  # 从页顶到 caption 顶部

                # 如果 caption 非常靠下 (> 70% 页高)，文字已经占满了当前页可用空间
                # 图片大部分在前一页，需要整个 required_height 从前一页取
                if cap_bbox.y0 > page_rect.height * 0.7:
                    need_from_prev = required_height
                else:
                    need_from_prev = required_height - available_on_curr

                if need_from_prev <= 0:
                    # 不需要跨页，fall through to normal extraction
                    cross_page = False
                else:
                    prev_page = doc[page_idx - 1]
                    prev_rect = prev_page.rect
                    # 前一页从底部往上取 need_from_prev 个点，不超过前一页高度
                    need_from_prev = min(need_from_prev, prev_rect.height)
                    if need_from_prev >= prev_rect.height * 0.8:
                        # 需要几乎整个前一页，说明图片整体都在前一页，从顶部开始取
                        prev_search_top = 0
                    else:
                        prev_search_top = max(0, prev_rect.height - need_from_prev)

                    # x0_same/x1_same/x0_other/x1_other already defined above

                    # 首次尝试：提取同栏
                    prev_region = fitz.Rect(x0_same, prev_search_top, x1_same, prev_rect.height)
                    mat = fitz.Matrix(dpi_scale, dpi_scale)
                    prev_pix = prev_page.get_pixmap(matrix=mat, clip=prev_region, alpha=False)

                    # 检查前一页同栏区域是否几乎全空白 (>99.99% 像素都是白色)
                    # 极度降低阈值：线条图大部分是白色，只需要很少的非空白像素就能判定有内容
                    prev_is_all_white = True
                    samples_prev = prev_pix.samples
                    non_white_count = sum(1 for pixel in samples_prev if pixel < 255)
                    if non_white_count < max(5, len(samples_prev) * 0.0001):
                        prev_is_all_white = True
                    else:
                        prev_is_all_white = False

                    chosen_x0 = x0_same
                    chosen_x1 = x1_same

                    # 如果同栏全空白且有另一栏可选，尝试提取另一栏
                    if prev_is_all_white and x0_other is not None:
                        if verbose:
                            print(f"    🔍 Figure {fig_num}: 前一页同栏全空白，尝试提取另一栏")
                        # 先尝试提取另一栏的底部区域（保留原prev_search_top
                        prev_region = fitz.Rect(x0_other, prev_search_top, x1_other, prev_rect.height)
                        prev_pix = prev_page.get_pixmap(matrix=mat, clip=prev_region, alpha=False)
                        # 更新x0/x1为另一栏的值
                        chosen_x0 = x0_other
                        chosen_x1 = x1_other
                        # 重新检查是否空白
                        samples_prev = prev_pix.samples
                        non_white_count = sum(1 for pixel in samples_prev if pixel < 255)
                        if non_white_count < max(5, len(samples_prev) * 0.0001):
                            prev_is_all_white = True
                        else:
                            prev_is_all_white = False

                    # 如果尝试了同栏+另一栏的底部区域仍然几乎全空白，说明图片整个都在前一页（不仅仅是底部）
                    # → 尝试提取整个前一页对应栏（从顶部到底部）
                    if prev_is_all_white:
                        if verbose:
                            print(f"    🔍 Figure {fig_num}: 前一页对应栏底部全空白，尝试提取整个前一页对应栏")
                        prev_region_full = fitz.Rect(chosen_x0, 0, chosen_x1, prev_rect.height)
                        prev_pix = prev_page.get_pixmap(matrix=mat, clip=prev_region_full, alpha=False)
                        samples_prev = prev_pix.samples
                        non_white_count = sum(1 for pixel in samples_prev if pixel < 255)
                        if non_white_count >= max(5, len(samples_prev) * 0.0001):
                            # 整个栏有非空白内容，使用整个前一页对应栏
                            prev_search_top = 0
                            prev_is_all_white = False
                        # else: 仍然空白，保持 prev_is_all_white = True，后续处理

                    # 不需要重置 chosen_x0/chosen_x1，保持之前选择的栏（同栏或另一栏）
                    x0 = chosen_x0
                    x1 = chosen_x1

                    # 渲染当前页顶部（从页头到 caption 顶部）
                    curr_region = fitz.Rect(x0, 0, x1, cap_bbox.y0)
                    curr_pix = page.get_pixmap(matrix=mat, clip=curr_region, alpha=False)

                    # 检查当前页区域是否几乎全空白 (>99.99% 像素都是白色)
                    curr_is_all_white = True
                    samples = curr_pix.samples
                    non_white_count_curr = sum(1 for pixel in samples if pixel < 255)
                    if non_white_count_curr < max(5, len(samples) * 0.0001):
                        curr_is_all_white = True
                    else:
                        curr_is_all_white = False

                    # 如果前一页和当前页拼接结果仍然几乎全空白，说明图片不在上方 → 尝试其他位置
                    total_non_white = (non_white_count if 'non_white_count' in locals() else 0) + non_white_count_curr
                    total_pixels = (len(samples_prev) if 'samples_prev' in locals() else 0) + len(samples)
                    if total_non_white < max(10, total_pixels * 0.0001):
                        # 几乎全空白 → 尝试其他位置
                        # 特殊情况：双栏排版，caption 在当前页右栏，图片可能在同一页另一栏（不跨页）
                        # 左栏先排版结束，caption 在右栏中部，图片完整在同一页左栏
                        page_width = page_rect.width
                        if x0_other is not None:
                            # 有另一栏，尝试提取整个当前页另一栏（从顶部到 caption 顶部）
                            if verbose:
                                print(f"    🔍 Figure {fig_num}: 原栏跨页提取全空白，尝试同一页另一栏（双栏错位排版）")
                            curr_region_other_full = fitz.Rect(x0_other, 0, x1_other, cap_bbox.y0)
                            curr_pix_other = page.get_pixmap(matrix=mat, clip=curr_region_other_full, alpha=False)
                            samples_other = curr_pix_other.samples
                            non_white_count_other = sum(1 for pixel in samples_other if pixel < 255)

                            if non_white_count_other >= max(5, len(samples_other) * 0.0001):
                                # 当前页另一栏有内容，整个图片就在这里，直接使用
                                curr_pix_other.save(str(out_path))
                                extracted_via = "same-page-other-col"
                                x0, x1 = x0_other, x1_other
                            else:
                                # 当前页另一栏也空白，尝试向下提取
                                if verbose:
                                    print(f"    🔍 Figure {fig_num}: 向上提取结果全空白，尝试向下提取（caption在图片上方）")
                                search_bottom = min(page_rect.height, cap_bbox.y1 + page_rect.height * search_above)
                                fig_region = fitz.Rect(x0, cap_bbox.y1, x1, search_bottom)
                                render_page_region(page, fig_region, out_path, dpi_scale)
                                extracted_via = "downward-after-blank"
                        else:
                            # 没有另一栏，尝试向下提取
                            if verbose:
                                print(f"    🔍 Figure {fig_num}: 向上提取结果全空白，尝试向下提取（caption在图片上方）")
                            search_bottom = min(page_rect.height, cap_bbox.y1 + page_rect.height * search_above)
                            fig_region = fitz.Rect(x0, cap_bbox.y1, x1, search_bottom)
                            render_page_region(page, fig_region, out_path, dpi_scale)
                            extracted_via = "downward-after-blank"
                    elif curr_is_all_white:
                        # 当前页没有图片内容，整个图片都在前一页，直接保存前一页
                        prev_pix.save(str(out_path))
                        extracted_via = "cross-page-prev-only"
                        if verbose:
                            print(f"    🔍 Figure {fig_num}: 当前页区域全空白，整个图片在前一页，仅使用前一页")
                    else:
                        # 拼接两页：prev 在上方，curr 在下方
                        height = prev_pix.h + curr_pix.h
                        width = max(prev_pix.w, curr_pix.w)
                        # 创建新 pixmap 并填充白色背景
                        # PyMuPDF 正确构造方式：Pixmap(colorspace, IRect(x0, y0, x1, y1), alpha)
                        rect = fitz.IRect(0, 0, width, height)
                        combined = fitz.Pixmap(prev_pix.colorspace, rect, prev_pix.alpha)
                        combined.clear_with(255)  # 填充白色背景
                        # 复制像素
                        combined.copy(prev_pix, (0, 0))
                        combined.copy(curr_pix, (0, prev_pix.h))
                        combined.save(str(out_path))
                        extracted_via = "cross-page-up"

            if not cross_page and extracted_via is None:
                # 正常情况：只在当前页提取
                # 估算图片区域（使用调整后的参数）
                fig_region = estimate_figure_bbox(page, cap_bbox, page_rect, search_above, margin_x)
                # 提取图片
                best_xref, best_overlap = find_best_raster_image(page, doc, fig_region)

                extracted_via = "raster"
                if best_xref and best_overlap > 500:  # 至少 500 sq pt 重叠
                    try:
                        extract_image_by_xref(doc, best_xref, out_path)
                    except Exception as e:
                        if verbose:
                            print(f"    ⚠ xref 提取失败 ({e})，切换渲染模式")
                        render_page_region(page, fig_region, out_path, dpi_scale)
                        extracted_via = "render"
                else:
                    render_page_region(page, fig_region, out_path, dpi_scale)
                    extracted_via = "render"

            results.append({
                "fig_num": fig_num,
                "chapter": int(cap_chapter),
                "seq": int(seq_num),
                "filename": filename,
                "page": page_idx + 1,
                "caption": task["caption"],
                "slug": slug,
                "via": extracted_via,
                "parameters": {"search_above": search_above, "margin_x": margin_x}
            })

            if verbose:
                icon = "📷" if extracted_via == "raster" else "🖼 "
                print(f"    {icon} Figure {fig_num} → {filename}  (p.{page_idx+1}, {extracted_via})")

        # 提取完成后，更新索引和验证任务（合并原有结果）
        # 读取原有索引
        index_path = out_dir / "index.json"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                existing_results = json.load(f)
            # 替换重试的结果
            for new_r in results:
                for i, old_r in enumerate(existing_results):
                    if old_r["fig_num"] == new_r["fig_num"]:
                        existing_results[i] = new_r
                        break
                else:
                    existing_results.append(new_r)
            results = existing_results

    else:
        # 正常模式：全页扫描提取
        for page_idx in pages:
            page = doc[page_idx]
            page_rect = page.rect
            captions = find_captions(page)

            if verbose and captions:
                print(f"  页 {page_idx+1}: 找到 {len(captions)} 个 caption")

            for cap in captions:
                fig_num = cap["num"]  # e.g. "3.2"

                # 验证章节号匹配
                parts = fig_num.split(".")
                if len(parts) != 2:
                    continue
                cap_chapter, seq_num = parts

                # 可选：只提取指定章节的图
                if chapter > 0 and int(cap_chapter) != chapter:
                    continue

                # 防重复
                if fig_num in seen_figs:
                    continue
                seen_figs.add(fig_num)

                # 生成文件名
                slug = slugify(cap["text"])
                filename = f"fig{cap_chapter}_{seq_num}-{slug}.png"
                out_path = out_dir / filename

                # 判断是否需要跨页：
                # 排版规则：图片永远在上，caption 永远在下
                # 情况 1：caption 在当前页顶部 → 图片的一部分在前一页底部 → 需要跨页拼接（图片在上，caption 在下）
                # 情况 2：caption 在当前页下部，caption 上方剩余空间不足放下整张图 → 图片一部分在前一页底部
                # 情况 3：caption 在栏底部（y0 > 70% 页高）→ 即使空间看起来够，文字已经占满，图片可能一部分在前一页底部
                cross_page = False
                search_above = 0.55
                margin_x = 30
                required_height = int(page_rect.height * search_above)
                available_on_curr = cap["bbox"].y0  # 从页顶到 caption 顶部的空间
                if cap["bbox"].y0 < page_rect.height * 0.15:
                    # 情况 1: caption 在页顶
                    if page_idx > 0:
                        cross_page = True
                        if verbose:
                            print(f"    📄 Figure {fig_num}: Caption在页顶，检测到跨页，拼接前一页底部")
                elif (available_on_curr < required_height * 0.8) or (cap["bbox"].y0 > page_rect.height * 0.7 and page_idx > 0):
                    # 情况 2/3:
                    # - 可用空间不足需要的 80%
                    # - 或者 caption 非常靠下（> 70%），即使空间够，文字占满了，图片需要跨页
                    if page_idx > 0:
                        cross_page = True
                        if available_on_curr < required_height * 0.8:
                            print(f"    📄 Figure {fig_num}: 图片空间不足，检测到跨页，拼接前一页底部")
                        else:
                            print(f"    📄 Figure {fig_num}: Caption接近栏底，检测到跨页，拼接前一页底部")

                if cross_page:
                    # 向上跨页拼接：前一页底部 + 当前页顶部
                    # caption 在当前页，图片从 caption 向上延伸，一部分进入前一页底部
                    required_height = int(page_rect.height * search_above)
                    available_on_curr = cap["bbox"].y0  # 从页顶到 caption 顶部
                    need_from_prev = required_height - available_on_curr
                    if need_from_prev <= 0:
                        # 不需要跨页
                        cross_page = False
                    else:
                        prev_page = doc[page_idx - 1]
                        prev_rect = prev_page.rect
                        # 前一页从底部往上取 need_from_prev 个点，不超过前一页高度
                        need_from_prev = min(need_from_prev, prev_rect.height)
                        prev_search_top = max(0, prev_rect.height - need_from_prev)

                        # 双栏排版检测：判断 caption 属于左栏还是右栏
                        # 如果整个 caption bbox 在中线左边 → 左栏
                        # 如果整个 caption bbox 在中线右边 → 右栏
                        # 如果跨中线 → 不限制，用完整宽度
                        page_width = page_rect.width
                        mid_page = page_width * 0.45
                        if cap["bbox"].x1 < mid_page:
                            # 整个 caption 在左栏，x 最大不超过中线
                            x0 = max(0, cap["bbox"].x0 - margin_x)
                            x1 = min(page_width * 0.5, cap["bbox"].x1 + margin_x)
                        elif cap["bbox"].x0 > mid_page:
                            # 整个 caption 在右栏，x 最小从中线开始
                            x0 = max(page_width * 0.4, cap["bbox"].x0 - margin_x)
                            x1 = min(page_width, cap["bbox"].x1 + margin_x)
                        else:
                            # caption 跨中线，不限制宽度
                            x0 = max(0, cap["bbox"].x0 - margin_x)
                            x1 = min(page_width, cap["bbox"].x1 + margin_x)

                        # 渲染前一页底部
                        prev_region = fitz.Rect(x0, prev_search_top, x1, prev_rect.height)
                        mat = fitz.Matrix(dpi_scale, dpi_scale)
                        prev_pix = prev_page.get_pixmap(matrix=mat, clip=prev_region, alpha=False)
                        # 渲染当前页顶部（从页头到 caption 顶部）
                        curr_region = fitz.Rect(x0, 0, x1, cap["bbox"].y0)
                        curr_pix = page.get_pixmap(matrix=mat, clip=curr_region, alpha=False)
                        # 拼接两页：prev 在上方，curr 在下方
                        height = prev_pix.h + curr_pix.h
                        width = max(prev_pix.w, curr_pix.w)
                        # 创建新 pixmap 并填充白色背景
                        # PyMuPDF 正确构造方式：Pixmap(colorspace, IRect(x0, y0, x1, y1), alpha)
                        rect = fitz.IRect(0, 0, width, height)
                        combined = fitz.Pixmap(prev_pix.colorspace, rect, prev_pix.alpha)
                        combined.clear_with(255)  # 填充白色背景
                        # 复制像素
                        combined.copy(prev_pix, (0, 0))
                        combined.copy(curr_pix, (0, prev_pix.h))
                        combined.save(str(out_path))
                        extracted_via = "cross-page-up"
                else:
                    # 正常情况：只在当前页提取
                    # 估算图片区域
                    fig_region = estimate_figure_bbox(page, cap["bbox"], page_rect, 0.55, 30)
                    # 优先提取嵌入光栅图
                    best_xref, best_overlap = find_best_raster_image(page, doc, fig_region)

                    extracted_via = "raster"
                    if best_xref and best_overlap > 500:  # 至少 500 sq pt 重叠
                        try:
                            extract_image_by_xref(doc, best_xref, out_path)
                        except Exception as e:
                            if verbose:
                                print(f"    ⚠ xref 提取失败 ({e})，切换渲染模式")
                            render_page_region(page, fig_region, out_path, dpi_scale)
                            extracted_via = "render"
                    else:
                        # 矢量图 fallback：渲染整个估算区域
                        render_page_region(page, fig_region, out_path, dpi_scale)
                        extracted_via = "render"

                # 保存 caption bbox 用于重试时调整
                cap_bbox_coords = [float(cap["bbox"].x0), float(cap["bbox"].y0), float(cap["bbox"].x1), float(cap["bbox"].y1)]

                results.append({
                    "fig_num": fig_num,
                    "chapter": int(cap_chapter),
                    "seq": int(seq_num),
                    "filename": filename,
                    "page": page_idx + 1,
                    "caption": cap["text"],
                    "slug": slug,
                    "via": extracted_via,
                    "caption_bbox": cap_bbox_coords,
                    "parameters": {"search_above": 0.55, "margin_x": 30}
                })

                if verbose:
                    icon = "📷" if extracted_via == "raster" else "🖼 "
                    print(f"    {icon} Figure {fig_num} → {filename}  (p.{page_idx+1}, {extracted_via})")

    doc.close()

    # 保存提取索引
    index_path = out_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 生成/更新验证任务
    verification_tasks = []
    for r in results:
        verification_tasks.append({
            "fig_num": r["fig_num"],
            "image_path": str(out_dir / r["filename"]),
            "caption": r["caption"],
            "page": r["page"],
            "caption_bbox": r.get("caption_bbox"),
            "parameters": r.get("parameters", {"search_above": 0.55, "margin_x": 30}),
            "verification": {
                "integrity": {
                    "description": "验证图片完整性：图片应只包含这张图，不包含多余文字/背景，完整显示整个图形，无裁切截断",
                    "status": "pending",
                    "result": None,
                    "comment": None
                },
                "caption_match": {
                    "description": "验证caption匹配：图片内容应与caption文字描述一致",
                    "status": "pending",
                    "result": None,
                    "comment": None
                }
            }
        })

    # 保存验证任务
    with open(verify_path, "w", encoding="utf-8") as f:
        json.dump(verification_tasks, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"\n✅ 共提取 {len(results)} 张图片")
        print(f"   索引：{index_path}")
        print(f"   光栅提取：{sum(1 for r in results if r['via']=='raster')} 张")
        print(f"   渲染裁剪：{sum(1 for r in results if r['via']=='render')} 张")
        print(f"   验证任务：{verify_path}（需AI视觉验证）")

    return results


def main():
    parser = argparse.ArgumentParser(description="从书籍PDF提取插图")
    parser.add_argument("pdf", help="输入PDF路径")
    parser.add_argument("chapter", type=int, nargs="?", default=0,
                        help="章节号（0=不过滤，提取全部）")
    parser.add_argument("--pages", help="页面范围，格式 START-END（1-based）")
    parser.add_argument("--output", default="figures", help="输出目录（默认: figures/）")
    parser.add_argument("--dpi", type=float, default=2.0, help="渲染分辨率倍率（默认: 2.0）")
    parser.add_argument("--retry-failed", action="store_true", help="只重新提取验证失败的图片")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")
    args = parser.parse_args()

    page_range = None
    if args.pages:
        parts = args.pages.split("-")
        page_range = (int(parts[0]) - 1, int(parts[1]) - 1)  # 转 0-based

    results = extract_figures_from_pdf(
        args.pdf,
        chapter=args.chapter,
        page_range=page_range,
        output_dir=args.output,
        dpi_scale=args.dpi,
        verbose=not args.quiet,
        retry_failed=args.retry_failed
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
