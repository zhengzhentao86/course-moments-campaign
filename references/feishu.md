# 飞书聊天交付

仅在当前用户要求或会话已有授权时发送。技能本身不包含发送授权，不包含固定收件人、App ID 或令牌。学习当前环境 lark-im/lark-shared 技能，或先执行 `lark-cli im +messages-send --help`、`lark-cli im images create --help` 核实命令能力。

## 操作顺序

1. 确认当前账户/机器人身份和唯一收件人。作者本人的历史 ID 不可随技能迁移。收件人不清楚就只问这一项，继续把本地产物做好。
2. 在本批工作目录串行上传已通过验收的图片，用该 CLI 支持的真实文件参数，通常 `--file ./posters/01.png`。文件路径不是 `@file` 内容引用。
3. 建立一条 `post`，标题只放便于识别的主题或发布日；正文是完整文案自然段，最后一行一张图片。不要混入内部点评、来源、评分、AI 标签或私有工具入口。
4. 串行发送；每条固定幂等键（如 campaign_id + post_id 的稳定短哈希），记录内容哈希、图片哈希、image_key、message_id 和状态。
5. 回读，核对每条正文、段落、唯一图片与对应关系，记录验证结果。成功项不要重复发送。

图文内容结构：

```json
{"zh_cn":{"title":"本条主题","content":[[{"tag":"text","text":"第一段"}],[{"tag":"text","text":"第二段"}],[{"tag":"img","image_key":"本次上传返回的真实键"}]]}}
```

本环境曾验证的命令形态（运行前核对当前 help；用结构化参数或安全文件传参，不让正文被 shell 展开）：

```text
lark-cli im images create --as bot --data '{"image_type":"message"}' --file ./posters/01.png
lark-cli im +messages-send --as bot --user-id <当前授权收件人> --msg-type post --content <上面的JSON> --idempotency-key <稳定键>
lark-cli im +messages-mget --as bot --message-ids <真实消息ID> --no-reactions
```

身份 `bot/user` 根据本环境实际授权选择，不默认为别人身份。用 Python `subprocess.run([...])` 等参数数组组装更安全；无 shell 拼接。运行结果同时检查退出码、顶层 `ok` 和逐项错误，不以退出码单独判断成功。

## 失败处理

- 上传成功后发送失败：保留 image_key，只补发送；发送成功验证失败：只回读，不重发。
- 超时或解析失败：可能已发送。先按真实 message_id 或当前会话记录核对；状态不明就报告待核，禁止全批重试。
- `mget` 内容可能是带图片标记的渲染字符串，不一定是 JSON。按返回契约解析，不能把字符串解析异常误判为未发送。
- 身份、权限、钥匙串或网络失败：保留完整本地产物和脱敏错误，说明缺口，协助修复 CLI。不能静默改成飞书云文档、改收件人或用浏览器绕过。
- 用户只要聊天消息时，不新建文档。压缩包可以补充，但不能替代逐条图文。

完成标准是实际消息回读通过；本地文案/图片完成、上传成功、发送成功和回读通过分别记录。
