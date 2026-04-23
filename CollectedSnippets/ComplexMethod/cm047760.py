def parse_template_string(
    template_string: str,
    keywords: Mapping[str, _Keyword],
    comment_tags: Collection[str],
    options: _JSOptions,
    lineno: int = 0,
    keyword: str = "",
) -> Generator[_ExtractionResult, None, None]:
    prev_character = None
    level = 0
    inside_str = False
    expression_contents = ''
    for character in template_string[1:-1]:
        if not inside_str and character in ('"', "'", '`'):
            inside_str = character
        elif inside_str == character and prev_character != r'\\':
            inside_str = False
        if level or keyword:
            expression_contents += character
        if not inside_str:
            if character == '{' and prev_character == '$':
                if keyword:
                    break
                level += 1
            elif level and character == '}':
                level -= 1
                if level == 0 and expression_contents:
                    expression_contents = expression_contents[0:-1]
                    fake_file_obj = io.BytesIO(expression_contents.encode())
                    yield from extract_javascript(fake_file_obj, keywords, comment_tags, options, lineno)
                    lineno += len(line_re.findall(expression_contents))
                    expression_contents = ''
        prev_character = character
    if keyword:
        yield (lineno, keyword, expression_contents, [])