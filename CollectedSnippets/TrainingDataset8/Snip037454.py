def _file_uploader(
        self,
        label: str,
        type: Optional[Union[str, List[str]]] = None,
        accept_multiple_files: bool = False,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        label_visibility: LabelVisibility = "visible",
        disabled: bool = False,
        ctx: Optional[ScriptRunContext] = None,
    ):
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=None, key=key, writes_allowed=False)
        maybe_raise_label_warnings(label, label_visibility)

        if type:
            if isinstance(type, str):
                type = [type]

            # May need a regex or a library to validate file types are valid
            # extensions.
            type = [
                file_type if file_type[0] == "." else f".{file_type}"
                for file_type in type
            ]

        file_uploader_proto = FileUploaderProto()
        file_uploader_proto.label = label
        file_uploader_proto.type[:] = type if type is not None else []
        file_uploader_proto.max_upload_size_mb = config.get_option(
            "server.maxUploadSize"
        )
        file_uploader_proto.multiple_files = accept_multiple_files
        file_uploader_proto.form_id = current_form_id(self.dg)
        if help is not None:
            file_uploader_proto.help = dedent(help)

        serde = FileUploaderSerde(accept_multiple_files)

        # FileUploader's widget value is a list of file IDs
        # representing the current set of files that this uploader should
        # know about.
        widget_state = register_widget(
            "file_uploader",
            file_uploader_proto,
            user_key=key,
            on_change_handler=on_change,
            args=args,
            kwargs=kwargs,
            deserializer=serde.deserialize,
            serializer=serde.serialize,
            ctx=ctx,
        )

        # This needs to be done after register_widget because we don't want
        # the following proto fields to affect a widget's ID.
        file_uploader_proto.disabled = disabled
        file_uploader_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )

        file_uploader_state = serde.serialize(widget_state.value)
        uploaded_file_info = file_uploader_state.uploaded_file_info
        if ctx is not None and len(uploaded_file_info) != 0:
            newest_file_id = file_uploader_state.max_file_id
            active_file_ids = [f.id for f in uploaded_file_info]

            ctx.uploaded_file_mgr.remove_orphaned_files(
                session_id=ctx.session_id,
                widget_id=file_uploader_proto.id,
                newest_file_id=newest_file_id,
                active_file_ids=active_file_ids,
            )

        self.dg._enqueue("file_uploader", file_uploader_proto)
        return widget_state.value