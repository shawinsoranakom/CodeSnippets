def remove_comments_and_empty_lines(content: str, file_type: str) -> str:
    """Remove comments and empty lines from a string of code, preserving newlines and URLs.

    Args:
        content (str): Code content to process.
        file_type (str): Type of file ('html', 'css', or 'js').

    Returns:
        (str): Cleaned content with comments and empty lines removed.

    Notes:
        Typical reductions for Ultralytics Docs are:
        - Total HTML reduction: 2.83% (1301.56 KB saved)
        - Total CSS reduction: 1.75% (2.61 KB saved)
        - Total JS reduction: 13.51% (99.31 KB saved)
    """
    if file_type == "html":
        content = HTML_COMMENT.sub("", content)  # Remove HTML comments
        # Preserve whitespace in <pre>, <code>, <textarea> tags
        preserved = []

        def preserve(match):
            """Mark HTML blocks that should not be minified."""
            preserved.append(match.group(0))
            return f"___PRESERVE_{len(preserved) - 1}___"

        content = HTML_PRESERVE.sub(preserve, content)
        content = HTML_TAG_SPACE.sub("><", content)  # Remove whitespace between tags
        content = HTML_MULTI_SPACE.sub(" ", content)  # Collapse multiple spaces
        content = HTML_EMPTY_LINE.sub("", content)  # Remove empty lines
        # Restore preserved content
        for i, text in enumerate(preserved):
            content = content.replace(f"___PRESERVE_{i}___", text)
    elif file_type == "css":
        content = CSS_COMMENT.sub("", content)  # Remove CSS comments
        # Remove whitespace around specific characters
        content = re.sub(r"\s*([{}:;,])\s*", r"\1", content)
        # Remove empty lines
        content = re.sub(r"^\s*\n", "", content, flags=re.MULTILINE)
        # Collapse multiple spaces to single space
        content = re.sub(r"\s{2,}", " ", content)
        # Remove all newlines
        content = re.sub(r"\n", "", content)
    elif file_type == "js":
        # Handle JS single-line comments (preserving http:// and https://)
        lines = content.split("\n")
        processed_lines = []
        for line in lines:
            # Only remove comments if they're not part of a URL
            if "//" in line and "http://" not in line and "https://" not in line:
                processed_lines.append(line.partition("//")[0])
            else:
                processed_lines.append(line)
        content = "\n".join(processed_lines)

        # Remove JS multi-line comments and clean whitespace
        content = re.sub(r"/\*[\s\S]*?\*/", "", content)
        # Remove empty lines
        content = re.sub(r"^\s*\n", "", content, flags=re.MULTILINE)
        # Collapse multiple spaces to single space
        content = re.sub(r"\s{2,}", " ", content)

        # Safe space removal around punctuation and operators (never include colons - breaks JS)
        content = re.sub(r"\s*([;{}])\s*", r"\1", content)
        content = re.sub(r"(\w)\s*\(|\)\s*{|\s*([+\-*/=])\s*", lambda m: m.group(0).replace(" ", ""), content)

    return content