def test_on_change_skips_empty_text(tmp_path: pathlib.Path):
    observer = _make_observer(tmp_path)
    key = mock.MagicMock()

    observer.on_change(key, {"text": ""}, time=0, is_addition=True)
    assert key not in observer.documents
    assert observer._skipped_count == 1
    assert observer._dirty is False

    observer.on_change(key, {"text": "   "}, time=0, is_addition=True)
    assert key not in observer.documents
    assert observer._skipped_count == 2
    assert observer._dirty is False

    observer.on_change(key, {"text": None}, time=0, is_addition=True)
    assert key not in observer.documents
    assert observer._skipped_count == 3
    assert observer._dirty is False

    observer.on_change(key, {"other": "value"}, time=0, is_addition=True)
    assert key not in observer.documents
    assert observer._skipped_count == 4
    assert observer._dirty is False