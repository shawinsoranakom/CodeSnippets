def _check_consistency(target: TokenizerLike, expected: TokenizerLike):
    assert isinstance(target, type(expected))

    # Cached attributes
    assert target.all_special_ids == expected.all_special_ids
    assert target.all_special_tokens == expected.all_special_tokens
    assert target.get_vocab() == expected.get_vocab()
    assert len(target) == len(expected)

    # Other attributes
    assert getattr(target, "padding_side", None) == getattr(
        expected, "padding_side", None
    )

    assert target.encode("prompt") == expected.encode("prompt")