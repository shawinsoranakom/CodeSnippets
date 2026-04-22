def test_remove_orphaned_files(self):
        """Test the remove_orphaned_files behavior"""
        f1 = self.mgr.add_file("session1", "widget1", FILE_1)
        f2 = self.mgr.add_file("session1", "widget1", FILE_1)
        f3 = self.mgr.add_file("session1", "widget1", FILE_1)
        self.assertEqual([f1, f2, f3], self.mgr.get_all_files("session1", "widget1"))

        # Nothing should be removed here (all files are active).
        self.mgr.remove_orphaned_files(
            "session1",
            "widget1",
            newest_file_id=f3.id,
            active_file_ids=[f1.id, f2.id, f3.id],
        )
        self.assertEqual([f1, f2, f3], self.mgr.get_all_files("session1", "widget1"))

        # Nothing should be removed here (no files are active, but they're all
        # "newer" than newest_file_id).
        self.mgr.remove_orphaned_files(
            "session1", "widget1", newest_file_id=f1.id - 1, active_file_ids=[]
        )
        self.assertEqual([f1, f2, f3], self.mgr.get_all_files("session1", "widget1"))

        # f2 should be removed here (it's not in the active file list)
        self.mgr.remove_orphaned_files(
            "session1", "widget1", newest_file_id=f3.id, active_file_ids=[f1.id, f3.id]
        )
        self.assertEqual([f1, f3], self.mgr.get_all_files("session1", "widget1"))

        # remove_orphaned_files on an untracked session/widget should not error
        self.mgr.remove_orphaned_files(
            "no_session", "no_widget", newest_file_id=0, active_file_ids=[]
        )