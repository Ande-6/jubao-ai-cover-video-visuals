import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILL_NAME = "jubao-ai-cover-video-visuals"


class ChineseLocalizationTests(unittest.TestCase):
    def setUp(self):
        self.files = [
            ROOT / "SKILL.md",
            ROOT / "INSTALL.md",
            ROOT / "agents" / "openai.yaml",
            ROOT / "references" / "prompt-structure.md",
            ROOT / "references" / "storyboard-and-consistency.md",
            ROOT / "references" / "cover-and-platform-layouts.md",
            ROOT / "references" / "visual-quality-checklist.md",
        ]

    def test_user_facing_files_are_chinese(self):
        for path in self.files:
            text = path.read_text(encoding="utf-8")
            cjk_count = sum("\u4e00" <= char <= "\u9fff" for char in text)
            self.assertGreaterEqual(cjk_count, 20, f"中文内容不足：{path}")

    def test_default_prompt_mentions_skill(self):
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn(f"${EXPECTED_SKILL_NAME}", text)

    def test_skill_name_matches_folder_and_frontmatter(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(ROOT.name, EXPECTED_SKILL_NAME)
        self.assertIn(f"name: {EXPECTED_SKILL_NAME}", text)

    def test_skill_routes_to_every_reference(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for name in (
            "prompt-structure.md",
            "storyboard-and-consistency.md",
            "cover-and-platform-layouts.md",
            "visual-quality-checklist.md",
        ):
            self.assertIn(name, text)

    def test_script_help_is_fully_chinese(self):
        for script in ("build_prompt_matrix.py", "validate_visual_plan.py"):
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / script), "--help"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("show this help message", result.stdout)
            self.assertIn("显示帮助信息", result.stdout)


if __name__ == "__main__":
    unittest.main()
