def test_ConfigItem_set_list(value, status):
    """ Test that lists validate and set correctly """
    default = ["TestDefault"]
    choices = ["TestDefault", "NewValue"]
    dtype = list
    dclass = ConfigItem(datatype=dtype,
                        default=default,
                        group=_TEST_GROUP,
                        info=_TEST_INFO,
                        choices=choices)

    with pytest.raises(ValueError):  # Confirm setting fails when name not set
        dclass.set(value)

    dclass.set_name("TestName")

    if status.startswith("success"):
        dclass.set(value)

        if not isinstance(value, list):
            value = [x.strip() for x in value.split(",")] if "," in value else value.split()
        assert dclass.value == dclass() == dclass.get()
        expected = [x.lower() for x in value]
        if status.startswith("success-fallback"):
            expected = [x.lower() for x in value if x in choices]
            if not expected:
                expected = [x.lower() for x in default]
        assert set(expected) == set(dclass.value)

    else:
        with pytest.raises(ValueError):
            dclass.set(value)