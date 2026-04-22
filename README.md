# 机器人学/深度学习书籍翻译项目

持续翻译多本机器人学、SLAM、强化学习、深度学习相关技术书籍的工作流项目。

## 项目结构

```
book-translate/
├── CLAUDE.md              # 全局翻译 pipeline 规则
├── README.md              # 本文件
├── glossary.md            # 全局统一术语表（所有书籍共用）
├── .claude/
│   └── skills/
│       ├── book-figure-extractor/       # 插图提取技能：从PDF提取插图并嵌入翻译文件
│       │   ├── SKILL.md
│       │   ├── scripts/
│       │   │   ├── extract_figures.py   # 提取图片到 figures/ 目录
│       │   │   └── inject_figures.py    # 将图片注入翻译 Markdown
│       │   └── references/
│       └── robotics-book-translator/    # 机器人学专业翻译技能
│           ├── SKILL.md
│           ├── scripts/
│           │   └── robotics_translate.py # 文本提取预处理工具
│           └── references/
│               └── robotics-glossary.md  # 机器人学术语对照表
└── books/                 # 各书籍翻译工作区
    └── book-name/
        ├── chapters/     # 原文待翻译章节
        ├── translated/   # 翻译完成输出
        └── figures/      # 提取的插图（每章一个目录）
```

## 工作流

### 翻译一本书

1. **准备**：在 `books/<book-name>/chapters/` 放入待翻译章节原文
2. **翻译**：使用 `robotics-book-translator` 技能逐章翻译，输出到 `books/<book-name>/translated/`
3. **提取插图**：使用 `book-figure-extractor` 从原PDF提取插图，嵌入到翻译后的 `.md` 文件
4. **更新术语表**：翻译完成后将新遇到的术语追加到 `glossary.md`

### 可用技能

- **robotics-book-translator**：专为机器人领域书籍翻译设计，保持公式完整、术语一致
- **book-figure-extractor**：从PDF提取插图，自动命名并嵌入到翻译 Markdown 对应位置

## 依赖安装

```bash
# 基础依赖
pip install PyMuPDF pdfplumber python-docx --break-system-packages
```

## 快速开始

```bash
# 1. 从PDF提取文本生成翻译草稿
python .claude/skills/robotics-book-translator/scripts/robotics_translate.py input.pdf --output draft.md

# 2. 翻译完成后，提取插图
python .claude/skills/book-figure-extractor/scripts/extract_figures.py book.pdf 3 --output figures

# 3. 将插图注入翻译文件
python .claude/skills/book-figure-extractor/scripts/inject_figures.py chapter_003.md figures/index.json
```

## 翻译规则

详见 [CLAUDE.md](./CLAUDE.md)：
- 保留所有 `$...$` 公式符号不翻译
- 公式数量前后必须一致
- 标题层级必须保留
- 翻译后更新全局术语表

## 术语表

全局统一术语表：[glossary.md](./glossary.md)，翻译所有书籍时必须遵循保证译名一致。
