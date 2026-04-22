def get_app(self):
        self.file_mgr = UploadedFileManager()
        return tornado.web.Application(
            [
                (
                    UPLOAD_FILE_ROUTE,
                    UploadFileRequestHandler,
                    dict(
                        file_mgr=self.file_mgr,
                        is_active_session=lambda session_id: True,
                    ),
                ),
            ]
        )