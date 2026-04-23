def test_read_params():
    """Check the behavior of the `_read_params` function."""
    out = _read_params("a", 1, tuple())
    assert out["param_type"] == "default"
    assert out["param_name"] == "a"
    assert out["param_value"] == "1"

    # check non-default parameters
    out = _read_params("a", 1, ("a",))
    assert out["param_type"] == "user-set"
    assert out["param_name"] == "a"
    assert out["param_value"] == "1"

    # check that we escape html tags
    tag_injection = "<script>alert('xss')</script>"
    out = _read_params("a", tag_injection, tuple())
    assert (
        out["param_value"]
        == "&quot;&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;&quot;"
    )
    assert out["param_name"] == "a"
    assert out["param_type"] == "default"