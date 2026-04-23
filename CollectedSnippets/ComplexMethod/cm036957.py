def test_enum_vs_int_disambiguation():
    # int stays primitive
    nf_int = normalize_value(1)
    assert nf_int == 1

    # enum becomes ("module.QualName", value)
    nf_enum = normalize_value(DummyLogprobsMode.RAW_LOGITS)
    assert isinstance(nf_enum, tuple) and len(nf_enum) == 2
    enum_type, enum_val = nf_enum
    assert enum_type.endswith(".DummyLogprobsMode")
    assert enum_val == "raw_logits"

    # Build factor dicts from configs with int vs enum
    f_int = get_hash_factors(SimpleConfig(1), set())
    f_enum = get_hash_factors(SimpleConfig(DummyLogprobsMode.RAW_LOGITS), set())
    # The int case remains a primitive value
    assert f_int["a"] == 1
    # The enum case becomes a tagged tuple ("module.QualName", "raw_logits")
    assert isinstance(f_enum["a"], tuple) and f_enum["a"][1] == "raw_logits"
    # Factor dicts must differ so we don't collide primitives with Enums.
    assert f_int != f_enum
    # Hash digests must differ correspondingly
    assert hash_factors(f_int) != hash_factors(f_enum)

    # Hash functions produce stable hex strings
    h_int = hash_factors(f_int)
    h_enum = hash_factors(f_enum)
    assert isinstance(h_int, str) and len(h_int) == 64
    assert isinstance(h_enum, str) and len(h_enum) == 64