def test_color_name_to_rgb_valid_name() -> None:
    """Test color_name_to_rgb."""
    assert color_util.color_name_to_rgb("red") == (255, 0, 0)

    assert color_util.color_name_to_rgb("blue") == (0, 0, 255)

    assert color_util.color_name_to_rgb("green") == (0, 128, 0)

    # spaces in the name
    assert color_util.color_name_to_rgb("dark slate blue") == (72, 61, 139)

    # spaces removed from name
    assert color_util.color_name_to_rgb("darkslateblue") == (72, 61, 139)
    assert color_util.color_name_to_rgb("dark slateblue") == (72, 61, 139)
    assert color_util.color_name_to_rgb("darkslate blue") == (72, 61, 139)