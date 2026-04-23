def simple_keyword_only_param_block(content, *, kwarg):
    return (
        "simple_keyword_only_param_block - Expected result (content value: %s): %s"
        % (
            content,
            kwarg,
        )
    )