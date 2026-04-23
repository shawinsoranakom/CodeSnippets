def test_all_incremental_commands_registered(self, todo_component):
        """All incremental commands should be registered."""
        commands = list(todo_component.get_commands())
        command_names = [c.names[0] for c in commands]

        assert "todo_add" in command_names
        assert "todo_set_status" in command_names
        assert "todo_update" in command_names
        assert "todo_delete" in command_names
        assert "todo_bulk_add" in command_names
        assert "todo_reorder" in command_names
        # todo_write is removed - incremental operations only
        assert "todo_write" not in command_names