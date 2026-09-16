#!/usr/bin/env python3
"""校验 AI 封面与视频配图视觉计划。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_RATIOS = {"16:9", "9:16", "1:1", "4:5"}
ALLOWED_RIGHTS = {"cleared", "original", "not_applicable"}
SHOT_FIELDS = (
    "shot_id",
    "purpose",
    "subject",
    "action",
    "environment",
    "camera",
    "lighting",
    "composition",
    "acceptance_checks",
)


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def is_nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_plan(plan: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return ["根节点必须是 JSON 对象"], warnings

    for key in ("project", "asset_type", "style"):
        if not is_nonempty(plan.get(key)):
            errors.append(f"{key}：必须是非空字符串")

    ratios = plan.get("aspect_ratios")
    if not isinstance(ratios, list) or not ratios:
        errors.append("aspect_ratios：必须是非空列表")
    else:
        for ratio in ratios:
            if ratio not in ALLOWED_RATIOS:
                errors.append(f"aspect_ratios：不支持的画幅 {ratio!r}")

    shots = plan.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("shots：必须是非空列表")
        shots = []
    ids = []
    for index, shot in enumerate(shots):
        if not isinstance(shot, dict):
            errors.append(f"shots[{index}]：必须是对象")
            continue
        for field in SHOT_FIELDS:
            value = shot.get(field)
            if field == "acceptance_checks":
                if not isinstance(value, list) or not value:
                    errors.append(f"shots[{index}].{field}：必须是非空列表")
            elif not is_nonempty(value):
                errors.append(f"shots[{index}].{field}：必须是非空字符串")
        if is_nonempty(shot.get("shot_id")):
            ids.append(shot["shot_id"])
    if len(ids) != len(set(ids)):
        errors.append("shots：存在重复的镜头编号 shot_id")

    continuity = plan.get("continuity")
    if not isinstance(continuity, dict):
        errors.append("continuity：必须是一致性档案对象")
        continuity = {}
    asset_type = plan.get("asset_type")
    subject_text = " ".join(
        [str(plan.get("project", "")), *(str(shot.get("subject", "")) for shot in shots if isinstance(shot, dict))]
    )
    is_character_plan = any(word in subject_text for word in ("人物", "女性", "男性", "女主", "男主", "双手"))
    is_product_plan = any(word in subject_text for word in ("产品", "商品", "包装", "咖啡机"))
    if asset_type == "video_storyboard" and len(shots) > 1 and is_character_plan:
        if not is_nonempty(continuity.get("character_identity")):
            errors.append("continuity.character_identity：多镜头人物计划缺少人物身份锚点")
        if not is_nonempty(continuity.get("wardrobe")):
            errors.append("continuity.wardrobe：多镜头人物计划缺少服装锚点")
    if is_product_plan and not is_nonempty(continuity.get("product_structure")):
        errors.append("continuity.product_structure：产品计划缺少产品结构锚点")
    for key in ("scene_anchors", "style_anchor"):
        if not is_nonempty(continuity.get(key)):
            errors.append(f"continuity.{key}：缺少一致性字段")
    if not isinstance(continuity.get("do_not_drift"), list) or not continuity.get("do_not_drift"):
        errors.append("continuity.do_not_drift：必须列出至少一个禁止漂移项")

    if asset_type == "cover":
        layout = plan.get("layout")
        if not isinstance(layout, dict):
            errors.append("layout：封面计划必须包含布局对象")
            layout = {}
        for key, label in (
            ("focal_point", "视觉焦点"),
            ("title_safe_area", "标题安全区"),
            ("brand_zone", "品牌区"),
        ):
            if not is_nonempty(layout.get(key)):
                errors.append(f"layout.{key}：封面缺少{label}")

    rights = plan.get("rights")
    if not isinstance(rights, dict) or rights.get("status") not in ALLOWED_RIGHTS:
        errors.append("rights.status：版权与肖像权状态必须是 cleared、original 或 not_applicable")

    text = plan.get("text", {})
    if isinstance(text, dict) and text.get("mode") == "verbatim":
        content = str(text.get("content", ""))
        if len(content) > 6:
            warnings.append("text.content：复杂文字建议改为 overlay 后期叠加")

    return sorted(errors), sorted(warnings)


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser.add_argument("plan", type=Path, help="视觉计划 JSON 文件")
    parser.add_argument("--strict", action="store_true", help="严格模式：把警告也视为失败")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="输出格式")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        errors, warnings = validate_plan(plan)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        for item in errors:
            print(f"错误：{item}")
        for item in warnings:
            print(f"警告：{item}")
        if not errors and not warnings:
            print("通过：视觉计划有效")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
