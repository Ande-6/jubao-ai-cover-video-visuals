---
name: jubao-ai-cover-video-visuals
description: 当用户需要创建 AI 封面、视频分镜配图、产品展示图、人物场景图、剧情图、图文卡片、多画幅视觉版本，或需要控制人物与品牌一致性时使用。
---

# Jubao AI 封面与视频配图助手

把主题、脚本或产品资料转换成可以生成、筛选和交付的连续视觉资产。先规划，再生成；多镜头任务不得逐张临时发挥。

## 工作流

1. 确认用途、平台、受众、交付数量、画幅和可用参考图。缺失信息不会改变范围时采用已标注默认值；会改变交付类型、人物身份或品牌规则时只问一个关键问题。
2. 创建视觉简报：主体、动作、环境、镜头、光线、构图、风格、色彩、材质和画幅。详细结构见 [references/prompt-structure.md](references/prompt-structure.md)。
3. 创建一致性档案。视频或系列图片必须锁定人物身份、服装、产品结构、场景锚点、品牌色和禁止漂移项。分镜规则见 [references/storyboard-and-consistency.md](references/storyboard-and-consistency.md)。
4. 封面任务定义视觉焦点、标题安全区、品牌区和缩略图可读性；多平台任务分别设计构图，不把简单裁切当作默认方案。读取 [references/cover-and-platform-layouts.md](references/cover-and-platform-layouts.md)。
5. 需要批量计划时，把视觉计划保存为 JSON，先运行 `python scripts/validate_visual_plan.py PLAN.json --strict`，再运行 `python scripts/build_prompt_matrix.py PLAN.json --format markdown`。
6. 使用当前环境可用的内置图片生成能力。单张、多个资产和多个变体都保持内置路径；“批量”本身不授权切换到需要 API Key 的方式。参考图必须标明角色：编辑目标、身份参考、产品参考、构图参考或风格参考。
7. 检查生成结果。读取 [references/visual-quality-checklist.md](references/visual-quality-checklist.md)，逐项核对人物、产品、文字、连续性、品牌、构图和权利风险。每次迭代只改变一个变量，并重复不可变项。
8. 交付最终图片路径、选中版本、每张图片的最终提示词、画幅、筛选理由、后期叠字说明和未解决限制。

## 文字与版权硬规则

- 复杂标题、价格、长文案和品牌标准字默认生成无字底图，再后期叠字；短标题也必须逐字检查。
- 不擅自使用真实人物肖像、受保护角色、竞争品牌标识或未经授权的在世艺术家风格。
- 不承诺模型能百分之百保持人物身份、文字或产品结构；必须通过实际检查才能交付。

## 常见错误

| 错误 | 纠正方式 |
|---|---|
| 逐镜头单独写提示词 | 先建一致性档案，再添加镜头变化。 |
| 横竖版只做裁切 | 为每种画幅单独规划主体位置和安全区。 |
| 把错字图片当成成品 | 使用无字底图和后期叠字方案。 |
| 只看“好不好看” | 按质检表检查结构、品牌和权利风险。 |
