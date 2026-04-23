def test_complete_migration_check_workflow(self, mock_inspect):
        """Test a complete migration check workflow."""
        mock_inspector = Mock()

        # Setup mock responses for different calls
        def get_table_names_side_effect():
            return ["users", "posts", "comments", "categories"]

        def get_columns_side_effect(table_name):
            columns_map = {
                "users": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "username", "type": "VARCHAR"},
                    {"name": "email", "type": "VARCHAR"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
                "posts": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "title", "type": "VARCHAR"},
                    {"name": "content", "type": "TEXT"},
                    {"name": "user_id", "type": "INTEGER"},
                ],
            }
            return columns_map.get(table_name, [])

        def get_foreign_keys_side_effect(table_name):
            fk_map = {"posts": [{"name": "fk_posts_user_id", "constrained_columns": ["user_id"]}]}
            return fk_map.get(table_name, [])

        def get_unique_constraints_side_effect(table_name):
            constraint_map = {
                "users": [
                    {"name": "uq_users_username", "column_names": ["username"]},
                    {"name": "uq_users_email", "column_names": ["email"]},
                ]
            }
            return constraint_map.get(table_name, [])

        mock_inspector.get_table_names.side_effect = get_table_names_side_effect
        mock_inspector.get_columns.side_effect = get_columns_side_effect
        mock_inspector.get_foreign_keys.side_effect = get_foreign_keys_side_effect
        mock_inspector.get_unique_constraints.side_effect = get_unique_constraints_side_effect
        mock_inspect.return_value = mock_inspector

        mock_conn = Mock()

        # Test complete migration check scenario
        # Check if tables exist
        assert table_exists("users", mock_conn) is True
        assert table_exists("posts", mock_conn) is True
        assert table_exists("nonexistent_table", mock_conn) is False

        # Check if required columns exist
        assert column_exists("users", "username", mock_conn) is True
        assert column_exists("users", "email", mock_conn) is True
        assert column_exists("posts", "user_id", mock_conn) is True
        assert column_exists("posts", "nonexistent_column", mock_conn) is False

        # Check if foreign keys exist
        assert foreign_key_exists("posts", "fk_posts_user_id", mock_conn) is True
        assert foreign_key_exists("posts", "nonexistent_fk", mock_conn) is False

        # Check if constraints exist
        assert constraint_exists("users", "uq_users_username", mock_conn) is True
        assert constraint_exists("users", "uq_users_email", mock_conn) is True
        assert constraint_exists("users", "nonexistent_constraint", mock_conn) is False