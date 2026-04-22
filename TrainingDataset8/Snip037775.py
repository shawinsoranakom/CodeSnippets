def save_element_message(
        self,
        delta_type: str,
        element_proto: Message,
        invoked_dg_id: str,
        used_dg_id: str,
        returned_dg_id: str,
    ) -> None:
        """Record the element protobuf as having been produced during any currently
        executing cached functions, so they can be replayed any time the function's
        execution is skipped because they're in the cache.
        """
        if not runtime.exists():
            return

        id_to_save = self.select_dg_to_save(invoked_dg_id, used_dg_id)
        for msgs in self._cached_message_stack:
            if isinstance(element_proto, Widget):
                wid = element_proto.id
                # TODO replace `Message` with a more precise type
                if not self._registered_metadata:
                    _LOGGER.error(
                        "Trying to save widget message that wasn't registered. This should not be possible."
                    )
                    raise AttributeError
                widget_meta = WidgetMsgMetadata(
                    wid, None, metadata=self._registered_metadata
                )
            else:
                widget_meta = None

            media_data = self._media_data

            if self._allow_widgets or widget_meta is None:
                msgs.append(
                    ElementMsgData(
                        delta_type,
                        element_proto,
                        id_to_save,
                        returned_dg_id,
                        widget_meta,
                        media_data,
                    )
                )

            # Reset instance state, now that it has been used for the
            # associated element.
            self._media_data = []
            self._registered_metadata = None
        for s in self._seen_dg_stack:
            s.add(returned_dg_id)