def _parse_op(self, name: str, args: dict[str, Any], total_dur: float) -> None:
        """Parse any CPU op into a generic OpRecord."""
        input_dims = args.get("Input Dims", [])
        input_strides = args.get("Input Strides", [])
        input_types = args.get("Input type", [])
        if not input_dims:
            return
        dtype_str = input_types[0] if input_types else ""
        dtype = _dtype_map.get(dtype_str)
        # Skip empty entries (non-tensor args like scalars/None) so the
        # tuples match what _get_node_input_shapes/strides extract from FX nodes.
        shapes = tuple(
            _to_nested_tuple(d)
            for d in input_dims
            if isinstance(d, (list, tuple)) and d
        )
        strides = tuple(
            _to_nested_tuple(d)
            for d in input_strides
            if isinstance(d, (list, tuple)) and d
        )
        if not shapes:
            return
        self.ops.append(
            OpRecord(
                op_name=name,
                input_shapes=shapes,
                input_strides=strides,
                dtype=dtype,
                duration_us=total_dur,
            )
        )