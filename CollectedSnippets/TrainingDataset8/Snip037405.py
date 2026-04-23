def deserialize(
        self, ui_value: Optional[FileUploaderStateProto], widget_id: str
    ) -> SomeUploadedSnapshotFile:
        file_recs = _get_file_recs_for_camera_input_widget(widget_id, ui_value)

        if len(file_recs) == 0:
            return_value = None
        else:
            return_value = UploadedFile(file_recs[0])
        return return_value