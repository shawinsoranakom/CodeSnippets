async def test_orphaned_upload_file_deletion(self):
        """An uploaded file with no associated AppSession should be
        deleted.
        """
        await self.runtime.start()

        client = MockSessionClient()
        session_id = self.runtime.create_session(client=client, user_info=MagicMock())

        file = UploadedFileRec(0, "file.txt", "type", b"123")

        # Upload a file for our connected session.
        added_file = self.runtime._uploaded_file_mgr.add_file(
            session_id=session_id,
            widget_id="widget_id",
            file=UploadedFileRec(0, "file.txt", "type", b"123"),
        )

        # The file should exist.
        self.assertEqual(
            self.runtime._uploaded_file_mgr.get_all_files(session_id, "widget_id"),
            [added_file],
        )

        # Disconnect the session. The file should be deleted.
        self.runtime.close_session(session_id)
        self.assertEqual(
            self.runtime._uploaded_file_mgr.get_all_files(session_id, "widget_id"),
            [],
        )

        # Upload a file for a session that doesn't exist.
        self.runtime._uploaded_file_mgr.add_file(
            session_id="no_such_session", widget_id="widget_id", file=file
        )

        # The file should be immediately deleted.
        self.assertEqual(
            self.runtime._uploaded_file_mgr.get_all_files(
                "no_such_session", "widget_id"
            ),
            [],
        )