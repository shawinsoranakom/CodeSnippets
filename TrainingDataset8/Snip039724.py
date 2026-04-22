def remove_files(_: int) -> None:
            self.media_file_manager.clear_session_refs("mock_session_id")
            self.media_file_manager.remove_orphaned_files()