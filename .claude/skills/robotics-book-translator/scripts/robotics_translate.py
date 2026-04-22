#!/usr/bin/env python3
"""
robotics_translate.py
快速预处理脚本：从 PDF/DOCX 提取文本，输出带结构标注的 Markdown，
供后续翻译使用。

用法：
    python scripts/robotics_translate.py input.pdf --output draft.md
    python scripts/robotics_translate.py input.docx --output draft.md --section 3
"""

import argparse
import sys
import re
from pathlib import Path


def extract_pdf(path: Path) -> str:
    """提取 PDF 文本，保留公式标记"""
    try:
        import pdfplumber
    except ImportError:
        print("请先安装: pip install pdfplumber --break-system-packages")
        sys.exit(1)

    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages.append(f"\n<!-- PAGE {i+1} -->\n{text}")
    return "\n".join(pages)


def extract_docx(path: Path) -> str:
    """提取 DOCX 文本，保留段落层级"""
    try:
        from docx import Document
    except ImportError:
        print("请先安装: pip install python-docx --break-system-packages")
        sys.exit(1)

    doc = Document(str(path))
    lines = []
    for para in doc.paragraphs:
        style = para.style.name
        text = para.text.strip()
        if not text:
            lines.append("")
            continue
        # 映射标题样式
        if style.startswith("Heading 1"):
            lines.append(f"# {text}")
        elif style.startswith("Heading 2"):
            lines.append(f"## {text}")
        elif style.startswith("Heading 3"):
            lines.append(f"### {text}")
        elif style.startswith("Heading 4"):
            lines.append(f"#### {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def annotate_formulas(text: str) -> str:
    """标注可能的公式区域（简单启发式）"""
    # 标注行内公式候选（含有 = 和数学符号的短语）
    math_pattern = re.compile(r'(\b[A-Z][a-z]?\s*[=≈≡∈]\s*[^.]{1,60})')
    text = math_pattern.sub(r'$\1$', text)
    return text


def count_figures(text: str) -> int:
    """统计文档中的图表引用数量"""
    figures = re.findall(r'[Ff]ig(?:ure)?\.?\s*\d+', text)
    tables = re.findall(r'[Tt]able\.?\s*\d+', text)
    return len(figures) + len(tables)


def generate_translation_template(text: str, source_file: str) -> str:
    """生成带翻译提示的 Markdown 模板"""
    n_figs = count_figures(text)
    header = f"""---
# 翻译工作文档
# 源文件：{source_file}
# 检测到图表引用数：{n_figs}
# 生成时间：自动生成
# 使用技能：robotics-book-translator
#
# 翻译说明：
# 1. 保留所有 $...$ 和 $$...$$ 公式，仅翻译周围文字
# 2. 图题格式：图 X.X：中文（英文原题）
# 3. 首次出现专业术语附英文：正向运动学（Forward Kinematics）
# 4. 代码块不翻译，仅翻译注释
---

"""
    return header + text


def main():
    parser = argparse.ArgumentParser(description="机器人书籍翻译预处理工具")
    parser.add_argument("input", help="输入文件路径 (.pdf 或 .docx)")
    parser.add_argument("--output", "-o", default="translation_draft.md",
                        help="输出 Markdown 文件路径")
    parser.add_argument("--section", "-s", type=int, default=None,
                        help="只提取第 N 章（近似，按页码分割）")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：文件不存在 {input_path}")
        sys.exit(1)

    suffix = input_path.suffix.lower()
    print(f"正在提取文本：{input_path}")

    if suffix == ".pdf":
        text = extract_pdf(input_path)
    elif suffix in (".docx", ".doc"):
        text = extract_docx(input_path)
    else:
        print(f"不支持的文件格式：{suffix}，支持 .pdf 和 .docx")
        sys.exit(1)

    print(f"提取完成，共 {len(text)} 字符")
    print(f"检测到图表引用：{count_figures(text)} 处")

    output_text = generate_translation_template(text, str(input_path))

    output_path = Path(args.output)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"翻译草稿已保存至：{output_path}")
    print("\n下一步：将此文件内容交给 Claude 进行翻译，")
    print("Claude 会遵循 robotics-book-translator 技能的格式规则。")


if __name__ == "__main__":
    main()
