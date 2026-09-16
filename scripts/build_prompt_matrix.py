#!/usr/bin/env python3
"""把视觉计划 JSON 转换成中文图片提示词矩阵。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


RATIO_GUIDANCE = {
    "16:9": "横版构图，保留横向叙事空间",
    "9:16": "竖版构图，主体集中在中部并避让顶部和底部界面",
    "1:1": "方形构图，四周保留安全裁切余量",
    "4:5": "信息流构图，主体略偏上并保留底部说明空间",
}


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def require_mapping(plan: dict, key: str) -> dict:
    value = plan.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} 必须是对象")
    return value


def require_list(plan: dict, key: str) -> list:
    value = plan.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} 必须是非空列表")
    return value


def make_row(plan: dict, shot: dict, ratio: str) -> dict:
    continuity = plan["continuity"]
    text = plan.get("text", {})
    prompt_parts = [
        f"环境：{shot.get('environment', '')}",
        f"主体：{shot.get('subject', '')}",
        f"人物身份：{continuity.get('character_identity', '不适用')}",
        f"服装：{continuity.get('wardrobe', '不适用')}",
        f"产品结构：{continuity.get('product_structure', '不适用')}",
        f"动作：{shot.get('action', '')}",
        f"镜头：{shot.get('camera', '')}",
        f"光线：{shot.get('lighting', '')}",
        f"构图：{shot.get('composition', '')}；{RATIO_GUIDANCE.get(ratio, '')}",
        f"风格：{plan.get('style', '')}；{continuity.get('style_anchor', '')}",
        f"色彩：{'、'.join(plan.get('palette', []))}",
        f"画幅：{ratio}",
    ]

    text_overlay = ""
    if text.get("mode") == "overlay" and text.get("content"):
        text_overlay = text["content"]
        prompt_parts.append("文字策略：无文字底图，无水印，保留清晰的后期标题安全区")
    elif text.get("mode") == "verbatim" and text.get("content"):
        prompt_parts.append(f"文字策略：准确文字“{text['content']}”，逐字正确，不得增加其他文字")
    else:
        prompt_parts.append("文字策略：无文字、无水印")

    do_not_drift = continuity.get("do_not_drift", [])
    if do_not_drift:
        prompt_parts.append(f"不可变项：{'、'.join(do_not_drift)}")

    negatives = [*plan.get("global_negative", []), "无关水印", "竞争品牌"]
    return {
        "shot_id": shot["shot_id"],
        "asset_type": plan["asset_type"],
        "aspect_ratio": ratio,
        "prompt": "。".join(part for part in prompt_parts if not part.endswith("：")) + "。",
        "negative_prompt": "、".join(dict.fromkeys(negatives)),
        "text_overlay": text_overlay,
        "acceptance_checks": shot.get("acceptance_checks", []),
    }


def build_rows(plan: dict) -> list[dict]:
    for key in ("project", "asset_type"):
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            raise ValueError(f"{key} 必须是非空字符串")
    require_mapping(plan, "continuity")
    shots = require_list(plan, "shots")
    ratios = require_list(plan, "aspect_ratios")
    rows = []
    for shot in shots:
        if not isinstance(shot, dict) or not shot.get("shot_id"):
            raise ValueError("每个镜头必须包含 shot_id")
        for ratio in ratios:
            rows.append(make_row(plan, shot, ratio))
    return rows


def render_markdown(rows: list[dict]) -> str:
    sections = ["# 图片提示词矩阵"]
    for row in rows:
        checks = "；".join(row["acceptance_checks"]) or "按视觉简报检查"
        overlay = row["text_overlay"] or "无"
        sections.append(
            f"## {row['shot_id']} · {row['aspect_ratio']}\n\n"
            f"- 资产类型：`{row['asset_type']}`\n"
            f"- 正向提示词：{row['prompt']}\n"
            f"- 负面约束：{row['negative_prompt']}\n"
            f"- 后期叠字：{overlay}\n"
            f"- 验收检查：{checks}"
        )
    return "\n\n".join(sections) + "\n"


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser.add_argument("plan", type=Path, help="视觉计划 JSON 文件")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="输出格式")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        rows = build_rows(plan)
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps({"rows": rows}, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(rows), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
