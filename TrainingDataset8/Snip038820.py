def test_check_callback_rules_error(self):
        with pytest.raises(StreamlitAPIException) as e:
            check_callback_rules(None, lambda x: x)

        assert "is not allowed." in str(e.value)