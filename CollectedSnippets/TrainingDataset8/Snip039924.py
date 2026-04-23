def test_validate_key(self):
        with pytest.raises(StreamlitAPIException) as e:
            require_valid_user_key(self.reserved_key)
        assert "are reserved" in str(e.value)