def test_message_with_time(source, message, is_long, time, time_str):
    out = _message_with_time(source, message, time)
    if is_long:
        assert len(out) > 70
    else:
        assert len(out) == 70

    assert out.startswith("[" + source + "] ")
    out = out[len(source) + 3 :]

    assert out.endswith(time_str)
    out = out[: -len(time_str)]
    assert out.endswith(", total=")
    out = out[: -len(", total=")]
    assert out.endswith(message)
    out = out[: -len(message)]
    assert out.endswith(" ")
    out = out[:-1]

    if is_long:
        assert not out
    else:
        assert list(set(out)) == ["."]