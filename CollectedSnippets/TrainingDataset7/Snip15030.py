def is_multiline_block_to_exclude(line):
        return _TOCTREE_DIRECTIVE_RE.match(line) or _PARSED_LITERAL_DIRECTIVE_RE.match(
            line
        )