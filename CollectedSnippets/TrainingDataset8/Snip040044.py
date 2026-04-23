def test_remove_orphaned_files(self):
        """`remove_orphaned_files` is thread-safe."""
        # Add a bunch of "active" files to a single widget
        active_file_ids = []
        for ii in range(self.NUM_THREADS):
            file = UploadedFileRec(id=0, name=f"file_{ii}", type="type", data=b"123")
            active_file_ids.append(self.mgr.add_file("session", "widget", file).id)

        # Now add some "inactive" files to the same widget
        inactive_file_ids = []
        for ii in range(self.NUM_THREADS, self.NUM_THREADS + 50):
            file = UploadedFileRec(id=0, name=f"file_{ii}", type="type", data=b"123")
            inactive_file_ids.append(self.mgr.add_file("session", "widget", file).id)

        newest_file_id = inactive_file_ids[len(inactive_file_ids) - 1] + 1

        # Call `remove_orphaned_files` from each thread.
        # Our active_files should remain intact, and our orphans should be removed!
        def remove_orphans(_: int) -> None:
            self.mgr.remove_orphaned_files(
                "session", "widget", newest_file_id, active_file_ids
            )
            remaining_ids = [
                file.id for file in self.mgr.get_all_files("session", "widget")
            ]
            self.assertEqual(sorted(active_file_ids), sorted(remaining_ids))

        call_on_threads(remove_orphans, num_threads=self.NUM_THREADS)