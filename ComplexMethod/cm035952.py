def test_invalid_email_with_special_chars(self):
        """Test that email with other special characters fails validation."""
        assert is_valid_email('user!name@example.com') is False
        assert is_valid_email('user#name@example.com') is False
        assert is_valid_email('user$name@example.com') is False
        assert is_valid_email('user&name@example.com') is False
        assert is_valid_email("user'name@example.com") is False
        assert is_valid_email('user*name@example.com') is False
        assert is_valid_email('user=name@example.com') is False
        assert is_valid_email('user^name@example.com') is False
        assert is_valid_email('user`name@example.com') is False
        assert is_valid_email('user{name@example.com') is False
        assert is_valid_email('user|name@example.com') is False
        assert is_valid_email('user}name@example.com') is False
        assert is_valid_email('user~name@example.com') is False