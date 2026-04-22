"""
将提取的图片嵌入到 chapter_xxx.md 翻译文件中。

用法:
    python inject_figures.py <chapter_xxx.md> <figures/index.json>
    python inject_figures.py chapter_003.md figures/index.json

策略：
1. 解析 index.json，建立 fig_num → 图片文件名 的映射
2. 逐行扫描 .md 文件，识别图题行（中文"图 X.Y"或英文"Figure X.Y"）
3. 在图题行**上方**插入 Markdown 图片引用
4. 找不到图题位置的图，追加到文件末尾（注释形式提示手动放置）
"""
import re
import json
import sys
import argparse
from pathlib import Path


# 匹配图题的正则（支持中文图题、英文 Figure、缩写 Fig.）
CAPTION_PATTERNS = [
    # 中文图题：图 3.2：... 或 图3.2 ...
    re.compile(r'(?:^|[^\w])图\s*([\d]+\.[\d]+)\s*[：:]\s*'),
    # 英文图题：Figure 3.2: ... 或 Fig. 3.2:
    re.compile(r'(?:Figure|Fig\.?)\s*([\d]+\.[\d]+)\s*[:\s]'),
]

def find_fig_num_in_line(line: str) -> str | None:
    """从行中提取图编号（如 '3.2'），找不到返回 None。"""
    for pattern in CAPTION_PATTERNS:
        m = pattern.search(line)
        if m:
            return m.group(1)
    return None


def build_img_tag(fig_info: dict, figures_dir: str = "figures") -> str:
    """构建 Markdown 图片引用行。"""
    filename = fig_info["filename"]
    fig_num = fig_info["fig_num"]
    slug = fig_info.get("slug", "figure")
    # alt text：用 slug 的可读形式
    alt = f"图{fig_num} {slug.replace('-', ' ')}"
    return f"![{alt}]({figures_dir}/{filename})"


def inject_figures(md_path: str, index_path: str, figures_dir: str = "figures", dry_run: bool = False):
    """
    主注入函数。
    
    Args:
        md_path:      翻译 Markdown 文件路径
        index_path:   figures/index.json 路径
        figures_dir:  图片目录相对路径（嵌入 md 时使用）
        dry_run:      True 时只预览不写文件
    """
    md_file = Path(md_path)
    if not md_file.exists():
        print(f"❌ 文件不存在: {md_path}")
        sys.exit(1)
    
    with open(index_path, encoding="utf-8") as f:
        figures = json.load(f)
    
    if not figures:
        print("⚠ index.json 为空，无图片可注入")
        return
    
    # 建立映射
    fig_map = {fig["fig_num"]: fig for fig in figures}
    
    lines = md_file.read_text(encoding="utf-8").split("\n")
    new_lines = []
    injected = {}    # fig_num → 注入到哪一行
    skipped = set()  # 已有图片引用的 fig_num（防止重复注入）
    
    for line_idx, line in enumerate(lines):
        # 检查此行是否已经是该图的图片引用（防止重复注入）
        if line.startswith("![") and "figures/" in line:
            # 尝试从 alt text 中解析 fig_num
            m = re.search(r'图([\d]+\.[\d]+)', line)
            if m:
                skipped.add(m.group(1))
        
        fig_num = find_fig_num_in_line(line)
        
        if fig_num and fig_num in fig_map and fig_num not in injected and fig_num not in skipped:
            fig = fig_map[fig_num]
            img_tag = build_img_tag(fig, figures_dir)
            # 在图题行上方插入：图片引用 + 空行
            new_lines.append(img_tag)
            new_lines.append("")
            injected[fig_num] = line_idx
        
        new_lines.append(line)
    
    # 处理未匹配的图
    missing = set(fig_map.keys()) - set(injected.keys()) - skipped
    if missing:
        new_lines.append("")
        new_lines.append("---")
        new_lines.append("")
        new_lines.append("<!-- ⚠ 以下图片未找到对应图题位置，请手动插入到合适位置 -->")
        for fig_num in sorted(missing):
            fig = fig_map[fig_num]
            img_tag = build_img_tag(fig, figures_dir)
            caption = fig.get("caption", "")
            new_lines.append(f"<!-- Figure {fig_num} (p.{fig['page']}): {caption} -->")
            new_lines.append(f"<!-- {img_tag} -->")
            new_lines.append("")
    
    result = "\n".join(new_lines)
    
    # 输出报告
    print(f"📄 文件：{md_path}")
    print(f"🗂  图片索引：{index_path}（共 {len(figures)} 张）")
    print(f"✅ 成功注入：{len(injected)} 张")
    if skipped:
        print(f"⏭  已有引用跳过：{len(skipped)} 张（{sorted(skipped)}）")
    if missing:
        print(f"⚠  未找到图题位置：{len(missing)} 张（{sorted(missing)}）")
    
    if dry_run:
        print("\n[Dry Run 模式] 以下为注入后内容预览（前 80 行）：")
        for i, line in enumerate(result.split("\n")[:80]):
            print(f"  {i+1:3d} | {line}")
        return
    
    # 备份原文件
    backup_path = md_file.with_suffix(".md.bak")
    md_file.rename(backup_path)
    print(f"💾 原文件备份至：{backup_path}")
    
    # 写入新内容
    md_file.write_text(result, encoding="utf-8")
    print(f"✍  已写入：{md_path}")


def main():
    parser = argparse.ArgumentParser(description="将提取图片注入到翻译 Markdown 文件")
    parser.add_argument("md", help="chapter_xxx.md 文件路径")
    parser.add_argument("index", help="figures/index.json 路径")
    parser.add_argument("--figures-dir", default="figures", help="图片目录（嵌入路径前缀，默认: figures）")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不修改文件")
    args = parser.parse_args()
    
    inject_figures(args.md, args.index, args.figures_dir, args.dry_run)


if __name__ == "__main__":
    main()
