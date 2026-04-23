def test_get_deps_info():
    with ignore_warnings():
        deps_info = _get_deps_info()

    assert "pip" in deps_info
    assert "setuptools" in deps_info
    assert "sklearn" in deps_info
    assert "numpy" in deps_info
    assert "scipy" in deps_info
    assert "Cython" in deps_info
    assert "pandas" in deps_info
    assert "matplotlib" in deps_info
    assert "joblib" in deps_info