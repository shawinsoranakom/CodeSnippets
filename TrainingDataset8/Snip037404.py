def serialize(
        self,
        snapshot: SomeUploadedSnapshotFile,
    ) -> FileUploaderStateProto:
        state_proto = FileUploaderStateProto()

        ctx = get_script_run_ctx()
        if ctx is None:
            return state_proto

        # ctx.uploaded_file_mgr._file_id_counter stores the id to use for
        # the *next* uploaded file, so the current highest file id is the
        # counter minus 1.
        state_proto.max_file_id = ctx.uploaded_file_mgr._file_id_counter - 1

        if not snapshot:
            return state_proto

        file_info: UploadedFileInfoProto = state_proto.uploaded_file_info.add()
        file_info.id = snapshot.id
        file_info.name = snapshot.name
        file_info.size = snapshot.size

        return state_proto