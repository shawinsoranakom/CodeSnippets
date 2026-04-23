def _enqueue(
        self,
        delta_type: str,
        element_proto: "Message",
        return_value: Union[None, Type[NoValue], Value] = None,
        last_index: Optional[Hashable] = None,
        element_width: Optional[int] = None,
        element_height: Optional[int] = None,
    ) -> Union["DeltaGenerator", None, Value]:
        """Create NewElement delta, fill it, and enqueue it.

        Parameters
        ----------
        delta_type: string
            The name of the streamlit method being called
        element_proto: proto
            The actual proto in the NewElement type e.g. Alert/Button/Slider
        return_value: any or None
            The value to return to the calling script (for widgets)
        element_width : int or None
            Desired width for the element
        element_height : int or None
            Desired height for the element

        Returns
        -------
        DeltaGenerator or any
            If this element is NOT an interactive widget, return a
            DeltaGenerator that can be used to modify the newly-created
            element. Otherwise, if the element IS a widget, return the
            `return_value` parameter.

        """
        # Operate on the active DeltaGenerator, in case we're in a `with` block.
        dg = self._active_dg
        # Warn if we're called from within a legacy @st.cache function
        legacy_caching.maybe_show_cached_st_function_warning(dg, delta_type)
        # Warn if we're called from within @st.memo or @st.singleton
        caching.maybe_show_cached_st_function_warning(dg, delta_type)

        # Warn if an element is being changed but the user isn't running the streamlit server.
        _maybe_print_use_warning()

        # Some elements have a method.__name__ != delta_type in proto.
        # This really matters for line_chart, bar_chart & area_chart,
        # since add_rows() relies on method.__name__ == delta_type
        # TODO: Fix for all elements (or the cache warning above will be wrong)
        proto_type = delta_type
        if proto_type in DELTA_TYPES_THAT_MELT_DATAFRAMES:
            proto_type = "vega_lite_chart"

        # Mirror the logic for arrow_ elements.
        if proto_type in ARROW_DELTA_TYPES_THAT_MELT_DATAFRAMES:
            proto_type = "arrow_vega_lite_chart"

        # Copy the marshalled proto into the overall msg proto
        msg = ForwardMsg_pb2.ForwardMsg()
        msg_el_proto = getattr(msg.delta.new_element, proto_type)
        msg_el_proto.CopyFrom(element_proto)

        # Only enqueue message and fill in metadata if there's a container.
        msg_was_enqueued = False
        if dg._root_container is not None and dg._cursor is not None:
            msg.metadata.delta_path[:] = dg._cursor.delta_path

            if element_width is not None:
                msg.metadata.element_dimension_spec.width = element_width
            if element_height is not None:
                msg.metadata.element_dimension_spec.height = element_height

            _enqueue_message(msg)
            msg_was_enqueued = True

        if msg_was_enqueued:
            # Get a DeltaGenerator that is locked to the current element
            # position.
            new_cursor = (
                dg._cursor.get_locked_cursor(
                    delta_type=delta_type, last_index=last_index
                )
                if dg._cursor is not None
                else None
            )

            output_dg = DeltaGenerator(
                root_container=dg._root_container,
                cursor=new_cursor,
                parent=dg,
            )
        else:
            # If the message was not enqueued, just return self since it's a
            # no-op from the point of view of the app.
            output_dg = dg

        # Save message for replay if we're called from within @st.memo or @st.singleton
        caching.save_element_message(
            delta_type,
            element_proto,
            invoked_dg_id=self.id,
            used_dg_id=dg.id,
            returned_dg_id=output_dg.id,
        )

        return _value_or_dg(return_value, output_dg)