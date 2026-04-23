def remove_orphans(_: int) -> None:
            self.mgr.remove_orphaned_files(
                "session", "widget", newest_file_id, active_file_ids
            )
            remaining_ids = [
                file.id for file in self.mgr.get_all_files("session", "widget")
            ]
            self.assertEqual(sorted(active_file_ids), sorted(remaining_ids))