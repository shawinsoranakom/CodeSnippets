def _get_buffer_info(self, name: str) -> tuple[Any, Any, Any, list, bool] | None:
        """Get buffer metadata (buf_obj, buf_size, buf_numel, actual_strides, is_contiguous).

        Returns None if the buffer doesn't exist.
        """
        buf_obj = V.graph.get_buffer(name)
        if buf_obj is None:
            return None
        buf_size = buf_obj.get_size()
        buf_numel = 1
        for s in buf_size:
            sval = self._safe_int(s)
            buf_numel *= sval if sval is not None else s

        # Get buffer strides and check contiguity
        actual_strides: list = []
        is_contiguous = True

        layout = getattr(buf_obj, "get_layout", lambda: None)()
        buf_stride = getattr(layout, "stride", None) if layout else None

        if buf_stride is not None:
            for i in range(len(buf_size)):
                actual_stride = self._safe_int(buf_stride[i])
                actual_strides.append(actual_stride)

            # Check contiguity
            if len(buf_size) == 1:
                if actual_strides[0] is not None and actual_strides[0] != 1:
                    is_contiguous = False
            elif len(buf_size) > 1:
                expected_stride = 1
                for i in range(len(buf_size) - 1, -1, -1):
                    actual_stride = actual_strides[i]
                    if actual_stride is None or actual_stride != expected_stride:
                        is_contiguous = False
                    dim_size = self._safe_int(buf_size[i])
                    if dim_size is not None:
                        expected_stride *= dim_size

        return buf_obj, buf_size, buf_numel, actual_strides, is_contiguous