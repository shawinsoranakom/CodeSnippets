def test_get_name_with_age_pass_int():
    with pytest.raises(TypeError):
        get_name_with_age("John", 30)