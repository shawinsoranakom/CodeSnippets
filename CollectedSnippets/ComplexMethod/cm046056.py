def _apply_markdown_style(content: str, style: list) -> str:
    """
    按照字体样式列表对文本内容应用 Markdown 格式。

    支持的样式：bold, italic, underline, strikethrough
    组合顺序（由内到外）：
      1. bold/italic（纯 Markdown，最内层，兼容性最广）
      2. strikethrough（~~，中间层，包裹纯 Markdown 符号广泛支持）
      3. underline（HTML <u>，最外层，作为 HTML 容器不干扰内部 Markdown 解析）

    这样可避免 `**~~<u>text</u>~~**` 在部分渲染器中因 HTML 标签打断
    外层 Markdown 标记解析而导致样式失效的问题，
    改为输出 `<u>~~**text**~~</u>`，兼容性更好。

    Args:
        content: 待格式化的文本内容
        style: 样式列表，如 ["bold", "italic"]

    Returns:
        str: 应用 Markdown 格式后的文本
    """
    if not style or not content:
        return content

    # 第一层（最内层）：bold / italic —— 纯 Markdown 符号，放最里面兼容性最好
    if 'bold' in style and 'italic' in style:
        content = f'***{content}***'
    elif 'bold' in style:
        content = f'**{content}**'
    elif 'italic' in style:
        content = f'*{content}*'

    # 第二层：strikethrough —— ~~text~~，包裹纯 Markdown 内容，广泛支持
    if 'strikethrough' in style:
        content = f'~~{content}~~'

    # 第三层（最外层）：underline —— markdown 无原生语法，使用 HTML <u> 标签
    # 作为外层 HTML 容器，不会干扰内部 Markdown 标记的解析
    if 'underline' in style:
        content = f'<u>{content}</u>'

    return content