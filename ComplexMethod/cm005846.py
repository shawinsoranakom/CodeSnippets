def test_multiple_columns_mixed_load_from_db(self):
        """Test creating multiple columns with different load_from_db settings."""
        columns = [
            Column(name="username", load_from_db=True, default="admin"),
            Column(name="email", load_from_db=True, default="user@example.com"),
            Column(name="role", load_from_db=False, default="user"),
            Column(name="active", load_from_db=False, default=True, type="boolean"),
        ]

        # Check load_from_db settings
        assert columns[0].load_from_db is True
        assert columns[1].load_from_db is True
        assert columns[2].load_from_db is False
        assert columns[3].load_from_db is False

        # Check defaults are preserved
        assert columns[0].default == "admin"
        assert columns[1].default == "user@example.com"
        assert columns[2].default == "user"
        assert columns[3].default is True