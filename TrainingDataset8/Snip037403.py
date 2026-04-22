def _get_file_recs_for_camera_input_widget(
    widget_id: str, widget_value: Optional[FileUploaderStateProto]
) -> List[UploadedFileRec]:
    if widget_value is None:
        return []

    ctx = get_script_run_ctx()
    if ctx is None:
        return []

    uploaded_file_info = widget_value.uploaded_file_info
    if len(uploaded_file_info) == 0:
        return []

    active_file_ids = [f.id for f in uploaded_file_info]

    # Grab the files that correspond to our active file IDs.
    return ctx.uploaded_file_mgr.get_files(
        session_id=ctx.session_id,
        widget_id=widget_id,
        file_ids=active_file_ids,
    )