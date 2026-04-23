def test_uuid_and_oot(tmp_path: Path):
    file_path = tmp_path / "_custom_mm_oot.py"
    file_path.write_text(IMPL_OOT_SRC)

    assert "impl_mm_oot" not in _custom_mm.impls
    _ = load_custom_mm_module(file_path)
    assert "impl_mm_oot" in _custom_mm.impls

    uuid = _custom_mm.impls["impl_mm_oot"].uuid()
    del _custom_mm.impls["impl_mm_oot"]

    # Replace file source
    file_path.write_text(IMPL_OOT_SRC + " # added file source")
    assert "impl_mm_oot" not in _custom_mm.impls
    _ = load_custom_mm_module(file_path)
    assert "impl_mm_oot" in _custom_mm.impls

    uuid1 = _custom_mm.impls["impl_mm_oot"].uuid()
    assert uuid1 != uuid
    del _custom_mm.impls["impl_mm_oot"]

    # Back to original
    file_path.write_text(IMPL_OOT_SRC)
    assert "impl_mm_oot" not in _custom_mm.impls
    _ = load_custom_mm_module(file_path)
    assert "impl_mm_oot" in _custom_mm.impls

    uuid2 = _custom_mm.impls["impl_mm_oot"].uuid()
    assert uuid2 == uuid
    assert uuid2 != uuid1
    del _custom_mm.impls["impl_mm_oot"]