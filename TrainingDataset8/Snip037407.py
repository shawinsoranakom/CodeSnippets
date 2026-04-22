def _camera_input(
        self,
        label: str,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext] = None,
    ) -> SomeUploadedSnapshotFile:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=None, key=key, writes_allowed=False)
        maybe_raise_label_warnings(label, label_visibility)

        camera_input_proto = CameraInputProto()
        camera_input_proto.label = label
        camera_input_proto.form_id = current_form_id(self.dg)

        if help is not None:
            camera_input_proto.help = dedent(help)

        serde = CameraInputSerde()

        camera_input_state = register_widget(
            "camera_input",
            camera_input_proto,
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
        camera_input_proto.disabled = disabled
        camera_input_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )

        ctx = get_script_run_ctx()
        camera_image_input_state = serde.serialize(camera_input_state.value)

        uploaded_shapshot_info = camera_image_input_state.uploaded_file_info

        if ctx is not None and len(uploaded_shapshot_info) != 0:
            newest_file_id = camera_image_input_state.max_file_id
            active_file_ids = [f.id for f in uploaded_shapshot_info]

            ctx.uploaded_file_mgr.remove_orphaned_files(
                session_id=ctx.session_id,
                widget_id=camera_input_proto.id,
                newest_file_id=newest_file_id,
                active_file_ids=active_file_ids,
            )

        self.dg._enqueue("camera_input", camera_input_proto)
        return camera_input_state.value