def deserialize(
        self, ui_value: Optional[FileUploaderStateProto], widget_id: str
    ) -> SomeUploadedFiles:
        file_recs = _get_file_recs(widget_id, ui_value)
        if len(file_recs) == 0:
            return_value: Optional[Union[List[UploadedFile], UploadedFile]] = (
                [] if self.accept_multiple_files else None
            )
        else:
            files = [UploadedFile(rec) for rec in file_recs]
            return_value = files if self.accept_multiple_files else files[0]
        return return_value