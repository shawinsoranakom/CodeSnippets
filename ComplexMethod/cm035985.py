def markdown_to_jira_markup(markdown_text: str) -> str:
    """
    Convert markdown text to Jira Wiki Markup format.
    This function handles common markdown elements and converts them to their
    Jira Wiki Markup equivalents. It's designed to be exception-safe.
    Args:
        markdown_text: The markdown text to convert
    Returns:
        str: The converted Jira Wiki Markup text
    """
    if not markdown_text or not isinstance(markdown_text, str):
        return ''

    try:
        # Work with a copy to avoid modifying the original
        text = markdown_text

        # Convert headers (# ## ### #### ##### ######)
        text = re.sub(r'^#{6}\s+(.*?)$', r'h6. \1', text, flags=re.MULTILINE)
        text = re.sub(r'^#{5}\s+(.*?)$', r'h5. \1', text, flags=re.MULTILINE)
        text = re.sub(r'^#{4}\s+(.*?)$', r'h4. \1', text, flags=re.MULTILINE)
        text = re.sub(r'^#{3}\s+(.*?)$', r'h3. \1', text, flags=re.MULTILINE)
        text = re.sub(r'^#{2}\s+(.*?)$', r'h2. \1', text, flags=re.MULTILINE)
        text = re.sub(r'^#{1}\s+(.*?)$', r'h1. \1', text, flags=re.MULTILINE)

        # Convert code blocks first (before other formatting)
        text = re.sub(
            r'```(\w+)\n(.*?)\n```', r'{code:\1}\n\2\n{code}', text, flags=re.DOTALL
        )
        text = re.sub(r'```\n(.*?)\n```', r'{code}\n\1\n{code}', text, flags=re.DOTALL)

        # Convert inline code (`code`)
        text = re.sub(r'`([^`]+)`', r'{{\1}}', text)

        # Convert markdown formatting to Jira formatting
        # Use temporary placeholders to avoid conflicts between bold and italic conversion

        # First convert bold (double markers) to temporary placeholders
        text = re.sub(r'\*\*(.*?)\*\*', r'JIRA_BOLD_START\1JIRA_BOLD_END', text)
        text = re.sub(r'__(.*?)__', r'JIRA_BOLD_START\1JIRA_BOLD_END', text)

        # Now convert single asterisk italics
        text = re.sub(r'\*([^*]+?)\*', r'_\1_', text)

        # Convert underscore italics
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'_\1_', text)

        # Finally, restore bold markers
        text = text.replace('JIRA_BOLD_START', '*')
        text = text.replace('JIRA_BOLD_END', '*')

        # Convert links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1|\2]', text)

        # Convert unordered lists (- or * or +)
        text = re.sub(r'^[\s]*[-*+]\s+(.*?)$', r'* \1', text, flags=re.MULTILINE)

        # Convert ordered lists (1. 2. etc.)
        text = re.sub(r'^[\s]*\d+\.\s+(.*?)$', r'# \1', text, flags=re.MULTILINE)

        # Convert strikethrough (~~text~~)
        text = re.sub(r'~~(.*?)~~', r'-\1-', text)

        # Convert horizontal rules (---, ***, ___)
        text = re.sub(r'^[\s]*[-*_]{3,}[\s]*$', r'----', text, flags=re.MULTILINE)

        # Convert blockquotes (> text)
        text = re.sub(r'^>\s+(.*?)$', r'bq. \1', text, flags=re.MULTILINE)

        # Convert tables (basic support)
        # This is a simplified table conversion - Jira tables are quite different
        lines = text.split('\n')
        in_table = False
        converted_lines = []

        for line in lines:
            if (
                '|' in line
                and line.strip().startswith('|')
                and line.strip().endswith('|')
            ):
                # Skip markdown table separator lines (contain ---)
                if '---' in line:
                    continue
                if not in_table:
                    in_table = True
                # Convert markdown table row to Jira table row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                converted_line = '|' + '|'.join(cells) + '|'
                converted_lines.append(converted_line)
            elif in_table and line.strip() and '|' not in line:
                in_table = False
                converted_lines.append(line)
            else:
                in_table = False
                converted_lines.append(line)

        text = '\n'.join(converted_lines)

        return text

    except Exception as e:
        # Log the error but don't raise it - return original text as fallback
        print(f'Error converting markdown to Jira markup: {str(e)}')
        return markdown_text or ''