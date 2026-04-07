def simple_keyword_only_default_block(content, *, kwarg=42):
    return (
        "simple_keyword_only_default_block - Expected result (content value: %s): %s"
        % (
            content,
            kwarg,
        )
    )