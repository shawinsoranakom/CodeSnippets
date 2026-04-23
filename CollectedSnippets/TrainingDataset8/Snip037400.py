def _download_button(
        self,
        label: str,
        data: DownloadButtonDataType,
        file_name: Optional[str] = None,
        mime: Optional[str] = None,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_click: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        ctx: Optional[ScriptRunContext] = None,
    ) -> bool:

        key = to_key(key)
        check_session_state_rules(default_value=None, key=key, writes_allowed=False)
        if is_in_form(self.dg):
            raise StreamlitAPIException(
                f"`st.download_button()` can't be used in an `st.form()`.{FORM_DOCS_INFO}"
            )

        download_button_proto = DownloadButtonProto()

        download_button_proto.label = label
        download_button_proto.default = False
        marshall_file(
            self.dg._get_delta_path_str(), data, download_button_proto, mime, file_name
        )

        if help is not None:
            download_button_proto.help = dedent(help)

        serde = ButtonSerde()

        button_state = register_widget(
            "download_button",
            download_button_proto,
            user_key=key,
            on_change_handler=on_click,
            args=args,
            kwargs=kwargs,
            deserializer=serde.deserialize,
            serializer=serde.serialize,
            ctx=ctx,
        )

        # This needs to be done after register_widget because we don't want
        # the following proto fields to affect a widget's ID.
        download_button_proto.disabled = disabled

        self.dg._enqueue("download_button", download_button_proto)
        return button_state.value