# 安装与使用

## 个人安装

把整个 `jubao-ai-cover-video-visuals` 文件夹复制到：

- Windows：`%USERPROFILE%\.codex\skills\jubao-ai-cover-video-visuals`
- macOS/Linux：`$HOME/.codex/skills/jubao-ai-cover-video-visuals`
- 自定义了 `CODEX_HOME` 时：`$CODEX_HOME/skills/jubao-ai-cover-video-visuals`

如果没有立即显示，重启 Codex。

## 项目安装

复制到项目根目录：

`<项目根目录>/.agents/skills/jubao-ai-cover-video-visuals`

个人目录适合在所有项目中使用；项目目录适合只让当前项目加载该 Skill。

## 调用示例

```text
$jubao-ai-cover-video-visuals

请为一条“便携咖啡机新品发布”短视频设计：
1 张竖版封面、3 个连续镜头配图，以及横版和方形适配版本。
品牌色为深绿和米白，人物与产品在所有镜头中保持一致。
```

默认使用当前环境提供的内置图片生成能力，不需要另外配置 API Key。只有明确选择命令行/API 路径时，才应讨论对应凭据。
