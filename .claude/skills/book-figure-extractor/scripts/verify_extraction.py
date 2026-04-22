#!/usr/bin/env python3
"""
图片提取验证脚本 - 使用Claude AI视觉能力进行验证

验证两个步骤：
1. 完整性验证：图片是否只包含完整图形，不包含多余部分，无截断
2. Caption匹配：图片内容与caption文字描述是否一致

用法:
    python verify_extraction.py <figures_dir>/verification_tasks.json

输出:
    更新 verification_tasks.json，写入验证结果，标记失败/通过
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional


def generate_verification_prompt(tasks: List[Dict]) -> str:
    """生成给Claude的验证提示词"""

    prompt = """你现在需要对提取出的书籍插图进行两项验证，请逐图检查：

## 验证规则

### 1. 完整性检查
- ✅ PASS: 图片只包含这张图的完整内容，不包含多余文字/背景，图形完整没有被截断
- ❌ FAIL: 图片只显示了图形的一部分，或者包含了多余的文字/其他图形，或者有大面积空白

### 2. Caption匹配检查
图片上的内容必须和caption文字描述一致：
- ✅ PASS: 图片内容与caption描述相符，caption说的就是这张图
- ❌ FAIL: 图片内容和caption对不上，这不是caption说的那张图

## 待验证图片列表
"""

    for i, task in enumerate(tasks):
        prompt += f"\n{i+1}. **Figure {task['fig_num']}**\n"
        prompt += f"   - Caption: {task['caption']}\n"
        prompt += f"   - Image file: {task['image_path']}\n"

    prompt += """
## 输出格式

请按以下JSON格式返回结果：
```json
{
  "results": [
    {
      "fig_num": "3.2",
      "integrity": {
        "pass": true,
        "comment": "完整显示DH坐标系示意图，无多余内容"
      },
      "caption_match": {
        "pass": true,
        "comment": "图内容是两连杆机械臂的DH坐标系分配，与caption一致"
      }
    },
    ...
  ]
}
```

只返回JSON，不要其他文字。
"""
    return prompt


def print_verification_summary(verified_tasks: List[Dict]) -> None:
    """打印验证结果汇总"""
    total = len(verified_tasks)
    integrity_pass = sum(1 for t in verified_tasks
                         if t["verification"]["integrity"]["result"] is True)
    integrity_fail = sum(1 for t in verified_tasks
                         if t["verification"]["integrity"]["result"] is False)
    match_pass = sum(1 for t in verified_tasks
                     if t["verification"]["caption_match"]["result"] is True)
    match_fail = sum(1 for t in verified_tasks
                     if t["verification"]["caption_match"]["result"] is False)
    pending = sum(1 for t in verified_tasks
                  if t["verification"]["integrity"]["status"] == "pending")

    print("\n" + "="*60)
    print("验证结果汇总")
    print("="*60)
    print(f"  总图片数: {total}")
    print(f"  完整性验证: {integrity_pass} 通过, {integrity_fail} 失败, {pending} 未验证")
    print(f"  Caption匹配: {match_pass} 通过, {match_fail} 失败, {pending} 未验证")
    print("-"*60)

    if integrity_fail + match_fail > 0:
        print("\n❌ 以下图片验证失败需要重新提取：")
        for t in verified_tasks:
            i_result = t["verification"]["integrity"]
            m_result = t["verification"]["caption_match"]
            if (i_result["result"] is False) or (m_result["result"] is False):
                fails = []
                if i_result["result"] is False:
                    fails.append(f"完整性: {i_result['comment']}")
                if m_result["result"] is False:
                    fails.append(f"匹配: {m_result['comment']}")
                print(f"  Figure {t['fig_num']}: {'; '.join(fails)}")
                print(f"    文件: {t['image_path']}")
    else:
        print("\n✅ 所有图片验证通过！")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="使用Claude AI视觉验证提取的图片"
    )
    parser.add_argument(
        "verification_file",
        help="verification_tasks.json 文件路径"
    )
    parser.add_argument(
        "--result", "-r",
        help="Claude返回的验证结果JSON文件（提供此参数表示导入结果）"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出结果文件（默认覆盖输入）"
    )
    args = parser.parse_args()

    # 读取验证任务
    verify_path = Path(args.verification_file)
    if not verify_path.exists():
        print(f"❌ 文件不存在: {verify_path}")
        sys.exit(1)

    with open(verify_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    if not tasks:
        print("⚠ 没有待验证任务")
        sys.exit(0)

    # 如果提供了结果文件，则导入结果并更新
    if args.result:
        result_path = Path(args.result)
        if not result_path.exists():
            print(f"❌ 结果文件不存在: {result_path}")
            sys.exit(1)

        with open(result_path, "r", encoding="utf-8") as f:
            try:
                result_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {e}")
                sys.exit(1)

        if "results" not in result_data:
            print(f"❌ 结果格式错误：缺少 'results' 字段")
            sys.exit(1)

        # 将结果更新回任务列表
        results = result_data["results"]
        updated = 0
        for result in results:
            fig_num = result["fig_num"]
            # 查找对应任务
            for task in tasks:
                if task["fig_num"] == fig_num:
                    # 更新完整性验证结果
                    if "integrity" in result:
                        task["verification"]["integrity"]["status"] = "completed"
                        task["verification"]["integrity"]["result"] = result["integrity"]["pass"]
                        task["verification"]["integrity"]["comment"] = result["integrity"].get("comment", "")
                    # 更新caption匹配结果
                    if "caption_match" in result:
                        task["verification"]["caption_match"]["status"] = "completed"
                        task["verification"]["caption_match"]["result"] = result["caption_match"]["pass"]
                        task["verification"]["caption_match"]["comment"] = result["caption_match"].get("comment", "")
                    updated += 1
                    break

        # 保存更新后的任务
        output_path = Path(args.output) if args.output else verify_path
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 已导入 {updated} 个验证结果，保存至: {output_path}")
        print_verification_summary(tasks)
        return 0

    # 生成提示词，让Claude进行视觉验证
    pending_tasks = [t for t in tasks if t["verification"]["integrity"]["status"] == "pending"]
    if not pending_tasks:
        print("✅ 所有任务已完成验证")
        print_verification_summary(tasks)
        sys.exit(0)

    print(f"\n📋 待验证: {len(pending_tasks)} 张图片\n")
    for t in pending_tasks:
        print(f"  - Figure {t['fig_num']}: {t['caption']}")
        print(f"    文件: {t['image_path']}")

    # 生成提示词，让Claude进行视觉验证
    prompt = generate_verification_prompt(pending_tasks)
    print("\n" + "="*60)
    print("以下是给Claude视觉验证的提示，请复制到Claude:")
    print("="*60 + "\n")
    print(prompt)
    print("\n" + "="*60)
    print("\n操作步骤:")
    print("1. 在Claude中粘贴上面的提示词")
    print("2. 使用 `/paste` 命令依次粘贴所有待验证的图片文件")
    print("3. Claude会返回JSON格式的验证结果")
    print("4. 将返回的完整JSON复制保存到文件 `result.json`")
    print("5. 运行导入结果:")
    print(f"   python {sys.argv[0]} {args.verification_file} --result result.json")
    print("\n完成验证后结果会写入 verification_tasks.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
