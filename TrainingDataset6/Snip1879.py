def get_code_block_lang(line: str) -> str:
    match = CODE_BLOCK_LANG_RE.match(line)
    if match:
        return match.group(1)
    return ""