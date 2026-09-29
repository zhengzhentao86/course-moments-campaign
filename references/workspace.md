# 资料与工作目录

以下文件由 AI 创建维护，不要求用户填表。本地证据和运行记录保存在项目里；可共享课程简介已内置在技能 `courses/`。首次使用本课程时读内置 brief.md/profile.json，在新工作目录初始化后由 AI 拷贝匹配档案作为起点；已有档案按来源日期合并，禁止无条件覆盖本地更新。

```text
<用户项目>/course-campaigns/<course-id>/
  course-profile.json        # 当前课程事实和风格覆盖，逐项附 source_ref
  feedback.jsonl            # 追加反馈、范围、来源和被替代关系
  evidence/                 # 私有原文和脱敏材料，禁止自动打包共享
  campaigns/<campaign-id>/
    campaign.json           # 以下格式，用于结构校验
    copy.json               # 用户需要的完整文案，或复用 campaign.posts
    朋友圈文案.md
    发布日历.md             # 倒计时才需要
    posters/01.png
    review.json             # 实际内容/视觉检查结果
    delivery-ledger.json    # 有发送授权时记录图片/消息/回读状态
```

同门课不同期可以复用稳定 course-id，新的日期和权益须按来源更新并存旧版本；不同课程新建 course-id。检索仅当前课程和相关风格，不遍历私人历史。

`course-profile.json` 的 `facts` 由 AI 按需填入 `audience`、`not_for`、`modules`（保留真实名称/顺序/上下游）、`exercises`、`deliverables`、`tools_and_rights`、`start_date`、`timezone`、`location` 等，每项以 `{value, source_ref, verified_at}` 或等价结构记录。缺失为 null/待核，不从历史样张填充。

## 辅助命令

以下 `<skill-dir>` 是本技能所在目录，不是固定用户路径。Python 3.9+ 无第三方依赖；反馈文件锁使用 macOS/Linux 的 fcntl，其他平台由 AI 使用该平台受支持的锁或串行记录方式。

```bash
python3 <skill-dir>/scripts/campaign.py init --workspace <新课程目录> --course-id <稳定ID> --name <课程名>
python3 <skill-dir>/scripts/campaign.py calendar --start-date 2027-01-05 --days 10
python3 <skill-dir>/scripts/campaign.py record-feedback --workspace <课程目录> --file <AI整理的反馈JSON>
python3 <skill-dir>/scripts/campaign.py check --file <本批campaign.json>
```

初始化拒绝覆盖已有目录；已有课程直接读取并增量更新。calendar 只计算本地自然日，不绑定系统今天，不自行排期发布；AI 先确定课程所在地时区和开课日期。`check --draft` 只检查草稿结构，不要求图片完成，不可用来宣称图文交付成功。

## campaign.json 最小格式

```json
{
  "campaign_id": "demo-2027",
  "course_id": "demo-course",
  "mode": "general",
  "expected_count": 1,
  "posts": [{
    "id": 1,
    "title": "具体主题",
    "text": "完整发布正文",
    "audience_problem": "目标读者的具体工作问题",
    "course_method": "来源中确实提供的课程方法",
    "practical_output": "现场动作或课后用法",
    "source_refs": ["课程简介中的对应段落"],
    "poster_prompt": "实际完整中文提示词",
    "image": "posters/01.png",
    "copy_reviewed": false,
    "visual_reviewed": false
  }]
}
```

倒计时增加顶层 `mode: countdown`、`start_date: YYYY-MM-DD`；逐条增加 `days: 10..1`、`publish_date`。图片为本批目录内的相对路径。制作前检查标记保持 false，真正看完图、检查文案后才写 true。该脚本仅检查结构和日期，不检查图片是不是正确海报，也不验证引用真实性、画像或营销效果。

## 单条反馈格式

```json
{
  "id": "feedback-001",
  "course_id": "demo-course",
  "kind": "editorial",
  "scope": "course",
  "rule_key": "business-specificity",
  "source_ref": "本轮用户消息的真实引用位置或本地证据文件",
  "summary": "脱敏后的真实反馈",
  "action": "下一轮具体怎么改",
  "status": "active",
  "supersedes": []
}
```

类型：editorial、course_fact、testimonial、measured_result、ai_suggestion。范围：batch、course、cross_course。batch 必须有 campaign_id；跨课程偏好须有用户明确范围原话 explicit_scope_quote，只允许 editorial。新记录替代旧记录必须同 course_id、scope、kind、rule_key；旧记录保留，加载时通过 supersedes 排除失效项。record-feedback 只追加，不会自动改课纲或生成新文案，AI 继续执行必要的档案更新与重写。
