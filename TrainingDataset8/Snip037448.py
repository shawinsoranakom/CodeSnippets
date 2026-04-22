def serialize(self, files: SomeUploadedFiles) -> FileUploaderStateProto:
        state_proto = FileUploaderStateProto()

        ctx = get_script_run_ctx()
        if ctx is None:
            return state_proto

        # ctx.uploaded_file_mgr._file_id_counter stores the id to use for
        # the *next* uploaded file, so the current highest file id is the
        # counter minus 1.
        state_proto.max_file_id = ctx.uploaded_file_mgr._file_id_counter - 1

        if not files:
            return state_proto
        elif not isinstance(files, list):
            files = [files]

        for f in files:
            file_info: UploadedFileInfoProto = state_proto.uploaded_file_info.add()
            file_info.id = f.id
            file_info.name = f.name
            file_info.size = f.size

        return state_proto