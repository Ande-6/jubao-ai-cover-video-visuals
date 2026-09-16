import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def sample_plan():
    return {
        "project": "咖啡机发布",
        "asset_type": "video_storyboard",
        "style": "自然写实商业摄影",
        "palette": ["深绿", "米白"],
        "continuity": {
            "character_identity": "28 岁女性，短黑发、圆框眼镜",
            "wardrobe": "米白衬衫、深绿围裙",
            "product_structure": "米白机身、黑色圆形旋钮、透明水箱",
            "scene_anchors": "浅木色厨房台面、米白墙面",
            "style_anchor": "自然写实、轻微景深",
            "do_not_drift": ["人物身份", "服装", "产品按钮数量"],
        },
        "aspect_ratios": ["16:9", "9:16"],
        "global_negative": ["多余手指", "文字乱码", "产品结构变化"],
        "text": {
            "content": "随时随地喝到新鲜咖啡，首发价 599 元",
            "mode": "overlay",
        },
        "rights": {"status": "original", "notes": "原创人物与产品概念"},
        "shots": [
            {
                "shot_id": "S01",
                "purpose": "引出产品",
                "subject": "女主与便携咖啡机",
                "action": "拿起产品",
                "environment": "清晨厨房",
                "camera": "中景，平视",
                "lighting": "左侧柔和晨光",
                "composition": "人物居左，右侧留白",
                "acceptance_checks": ["人物身份一致", "旋钮数量正确"],
            },
            {
                "shot_id": "S02",
                "purpose": "展示操作",
                "subject": "双手与便携咖啡机",
                "action": "旋转黑色圆形旋钮",
                "environment": "同一厨房台面",
                "camera": "手部特写，轻微俯拍",
                "lighting": "同方向柔和晨光",
                "composition": "产品居中，操作清晰",
                "acceptance_checks": ["产品结构一致", "手指完整"],
            },
        ],
    }


class PromptMatrixTests(unittest.TestCase):
    def test_build_rows_combines_continuity_shot_and_ratio(self):
        from build_prompt_matrix import build_rows

        rows = build_rows(sample_plan())
        self.assertEqual(len(rows), 4)
        self.assertIn("短黑发、圆框眼镜", rows[0]["prompt"])
        self.assertIn("拿起产品", rows[0]["prompt"])
        self.assertIn("16:9", rows[0]["prompt"])
        self.assertEqual(rows[0]["shot_id"], "S01")
        self.assertEqual(rows[1]["aspect_ratio"], "9:16")
        self.assertEqual(rows[2]["shot_id"], "S02")

    def test_overlay_text_requests_text_free_base_image(self):
        from build_prompt_matrix import build_rows

        rows = build_rows(sample_plan())
        self.assertIn("无文字底图", rows[0]["prompt"])
        self.assertEqual(rows[0]["text_overlay"], "随时随地喝到新鲜咖啡，首发价 599 元")
        self.assertIn("文字乱码", rows[0]["negative_prompt"])

    def test_short_verbatim_text_stays_in_prompt(self):
        from build_prompt_matrix import build_rows

        plan = sample_plan()
        plan["text"] = {"content": "新品上市", "mode": "verbatim"}
        row = build_rows(plan)[0]
        self.assertIn('准确文字“新品上市”', row["prompt"])
        self.assertEqual(row["text_overlay"], "")

    def test_cli_emits_utf8_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "plan.json"
            source.write_text(json.dumps(sample_plan(), ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_prompt_matrix.py"), str(source), "--format", "json"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("短黑发", result.stdout)
            self.assertNotIn("\\u77ed", result.stdout)


class VisualPlanValidationTests(unittest.TestCase):
    def test_valid_storyboard_passes(self):
        from validate_visual_plan import validate_plan

        errors, warnings = validate_plan(sample_plan())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_character_story_requires_identity_anchor(self):
        from validate_visual_plan import validate_plan

        plan = sample_plan()
        plan["continuity"].pop("character_identity")
        errors, _ = validate_plan(plan)
        self.assertTrue(any("人物身份锚点" in item for item in errors))

    def test_product_story_requires_product_structure(self):
        from validate_visual_plan import validate_plan

        plan = sample_plan()
        plan["continuity"].pop("product_structure")
        errors, _ = validate_plan(plan)
        self.assertTrue(any("产品结构锚点" in item for item in errors))

    def test_cover_requires_layout_safe_areas(self):
        from validate_visual_plan import validate_plan

        plan = sample_plan()
        plan["asset_type"] = "cover"
        plan["shots"] = [plan["shots"][0]]
        plan["layout"] = {"focal_point": "产品", "brand_zone": "左上角"}
        errors, _ = validate_plan(plan)
        self.assertTrue(any("标题安全区" in item for item in errors))

    def test_unresolved_rights_risk_is_blocking(self):
        from validate_visual_plan import validate_plan

        plan = sample_plan()
        plan["rights"] = {"status": "unknown", "notes": ""}
        errors, _ = validate_plan(plan)
        self.assertTrue(any("版权" in item for item in errors))

    def test_invalid_ratio_and_duplicate_shot_id_fail(self):
        from validate_visual_plan import validate_plan

        plan = sample_plan()
        plan["aspect_ratios"].append("3:2")
        plan["shots"][1]["shot_id"] = "S01"
        errors, _ = validate_plan(plan)
        self.assertTrue(any("画幅" in item for item in errors))
        self.assertTrue(any("重复" in item for item in errors))


class ExampleIntegrationTests(unittest.TestCase):
    def test_product_launch_example_validates_and_generates_twelve_rows(self):
        from build_prompt_matrix import build_rows, render_markdown
        from validate_visual_plan import validate_plan

        source = ROOT / "examples" / "product-launch-plan.json"
        expected_output = ROOT / "examples" / "product-launch-output.md"
        plan = json.loads(source.read_text(encoding="utf-8"))
        errors, warnings = validate_plan(plan)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        rows = build_rows(plan)
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["aspect_ratio"] for row in rows}, {"16:9", "9:16", "1:1"})
        self.assertEqual(expected_output.read_text(encoding="utf-8"), render_markdown(rows))

    def test_example_cli_strict_validation_passes(self):
        source = ROOT / "examples" / "product-launch-plan.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_visual_plan.py"), str(source), "--strict"],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("通过", result.stdout)


if __name__ == "__main__":
    unittest.main()
