def test_slugify() -> None:
    """Test slugify."""
    assert util.slugify("T-!@#$!#@$!$est") == "t_est"
    assert util.slugify("Test More") == "test_more"
    assert util.slugify("Test_(More)") == "test_more"
    assert util.slugify("Tèst_Mörê") == "test_more"
    assert util.slugify("B8:27:EB:00:00:00") == "b8_27_eb_00_00_00"
    assert util.slugify("test.com") == "test_com"
    assert util.slugify("greg_phone - exp_wayp1") == "greg_phone_exp_wayp1"
    assert (
        util.slugify("We are, we are, a... Test Calendar")
        == "we_are_we_are_a_test_calendar"
    )
    assert util.slugify("Tèst_äöüß_ÄÖÜ") == "test_aouss_aou"
    assert util.slugify("影師嗎") == "ying_shi_ma"
    assert util.slugify("けいふぉんと") == "keihuonto"
    assert util.slugify("$") == "unknown"
    assert util.slugify("Ⓐ") == "a"
    assert util.slugify("ⓑ") == "b"
    assert util.slugify("$$$") == "unknown"
    assert util.slugify("$something") == "something"
    assert util.slugify("") == ""
    assert util.slugify(None) == ""