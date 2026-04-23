def code_content_clean(content):
    """清理代码内容，移除Markdown代码块的开始和结束标记"""
    if not content:
        return ""

    lines = content.splitlines()
    start_idx = 0
    end_idx = len(lines)

    if lines and lines[0].startswith("```"):
        start_idx = 1

    if lines and end_idx > start_idx and lines[end_idx - 1].strip() == "```":
        end_idx -= 1

    if start_idx < end_idx:
        return "\n".join(lines[start_idx:end_idx]).strip()
    return ""