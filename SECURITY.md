# Security / 安全问题

For a vulnerability, use this repository's GitHub **Security → Report a vulnerability**
when available. If it is unavailable, contact the maintainer through the public
GitHub profile and request a private reporting channel before sharing details.

Do not include secrets, personal video, local usernames or tokenized URLs in public
issues. Ordinary bugs can use the issue template with synthetic reproduction data.

The preview server binds to `127.0.0.1` and serves the selected directory. The HTML
renderer disables raw Markdown HTML and external Markdown images, while escaping
embedded evidence JSON. These controls are not a general sandbox for untrusted media.

安全漏洞请优先使用 GitHub 私密报告入口；公开 issue 使用不含个人信息的复现。
