def post(self, **kwargs):
        """Receive an uploaded file and add it to our UploadedFileManager.
        Return the file's ID, so that the client can refer to it."""
        args: Dict[str, List[bytes]] = {}
        files: Dict[str, List[Any]] = {}

        tornado.httputil.parse_body_arguments(
            content_type=self.request.headers["Content-Type"],
            body=self.request.body,
            arguments=args,
            files=files,
        )

        try:
            session_id = self._require_arg(args, "sessionId")
            widget_id = self._require_arg(args, "widgetId")
            if not self._is_active_session(session_id):
                raise Exception(f"Invalid session_id: '{session_id}'")

        except Exception as e:
            self.send_error(400, reason=str(e))
            return

        # Create an UploadedFile object for each file.
        # We assign an initial, invalid file_id to each file in this loop.
        # The file_mgr will assign unique file IDs and return in `add_file`,
        # below.
        uploaded_files: List[UploadedFileRec] = []
        for _, flist in files.items():
            for file in flist:
                uploaded_files.append(
                    UploadedFileRec(
                        id=0,
                        name=file["filename"],
                        type=file["content_type"],
                        data=file["body"],
                    )
                )

        if len(uploaded_files) != 1:
            self.send_error(
                400, reason=f"Expected 1 file, but got {len(uploaded_files)}"
            )
            return

        added_file = self._file_mgr.add_file(
            session_id=session_id, widget_id=widget_id, file=uploaded_files[0]
        )

        # Return the file_id to the client. (The client will parse
        # the string back to an int.)
        self.write(str(added_file.id))
        self.set_status(200)