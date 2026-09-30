# 课程朋友圈文案与海报

输入一句任务，基于内置课程生成自然、具体的朋友圈文案与一对一配套海报。支持系列宣传、配套工具、真实学员反馈、开课倒计时，以及授权后的飞书聊天图文交付。

当前版本：1.1.1。公开仓库，可直接克隆安装，无需 GitHub 登录或仓库邀请。

## 直接使用

> 使用 $course-moments-campaign，用内置课程简介做20组朋友圈文案与海报，沿用清爽画风，通过飞书发给我。

> 这门课改成新一期，日期是……。更新技能里的简介，再做开课前10天到1天的宣传。

> 这是另一门课的简介：……。沿用文案与画风规则，按新课内容做。

## 安装与更新

安装前准备支持 SKILL.md 的 AI 工具、内置图像生成能力；使用飞书资料或交付时，需要安装并登录 lark-cli。Python辅助脚本无需第三方依赖。

Codex 首次安装（目标目录须不存在）：

```bash
git clone https://github.com/zhengzhentao86/course-moments-campaign.git ~/.codex/skills/course-moments-campaign
```

已经通过 Git 克隆安装：

```bash
git -C ~/.codex/skills/course-moments-campaign pull --ff-only
```

如果已有非 Git 版本或本地修改，先备份合并，不能直接覆盖。也可下载 Release 安装包。新开任务后使用技能，或直接让 AI 读取 SKILL.md。

## 里面有什么

- [内置课程简介](courses/ai-commerce-workshop/brief.md)：受众、8模块、现场动作、本期安排与宣传重点。
- [工具说明](courses/ai-commerce-workshop/tools.md)：工具与业务场景衔接。
- [助理使用说明](references/assistant-guide.md)：安装、调用与反馈。
- [技能执行规则](SKILL.md)：完整制作和验收流程。
- [版本记录](CHANGELOG.md)：后续课程与技能变更。
- assets/：已认可系统篇、工具篇、倒计时篇海报。

本期时间为2026年10月10—11日广州，新的课程或新一期需使用新事实。课程简介可以直接使用；样图里的日期不能无条件复用。

## 更新规则

用户提供新简介或修改意见，AI维护 courses/ 中对应课程资料，校验并按授权发布新版本。助理拉取更新即可获得可共享资料。原始客户私聊、账号密码、收件人信息和本地发送记录不进入仓库。未提供真实数据时，不能声称宣传带来了成交增长。

## 检查

```bash
python3 evals/test_campaign.py
```

脚本验证日期与数据结构；实际海报仍需逐张查看，飞书交付仍需发送回读。模拟用例不能写进真实课程反馈。
