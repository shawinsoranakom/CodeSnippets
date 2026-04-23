def _check_store_needs_transpose(self, name: str) -> bool:
        """
        Check if output needs transpose for column-major storage.

        Transpose on store is needed when:
        - Output has column-major stride (s0 < s1)
        - But input(s) have row-major stride
        - And we haven't already transposed on load
        """
        if self.permuted_input_buffers:
            return False

        info = self._get_buffer_info(name)
        if info is None:
            return False

        _, buf_size, _, actual_strides, _ = info
        if len(actual_strides) != 2 or len(buf_size) != 2:
            return False

        size0 = self._safe_int(buf_size[0])
        size1 = self._safe_int(buf_size[1])
        s0 = actual_strides[0]
        s1 = actual_strides[1]

        # Check if output is column-major with valid dimensions
        if not (
            s0 is not None
            and s1 is not None
            and s0 < s1
            and size0 is not None
            and size1 is not None
            and size0 > 1
            and size1 > 1
        ):
            return False

        # Check if any input is column-major (if so, no transpose needed)
        for inp_name in self.args.input_buffers:
            inp_info = self._get_buffer_info(inp_name)
            if inp_info is None:
                continue
            _, _, _, inp_strides, _ = inp_info
            if len(inp_strides) != 2:
                continue
            inp_s0 = inp_strides[0]
            inp_s1 = inp_strides[1]
            if inp_s0 is not None and inp_s1 is not None and inp_s0 < inp_s1:
                return False  # Input is also column-major

        return True