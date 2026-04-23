def _codegen_strided_reshapes(
        self, code: IndentedBuffer, params: list[str]
    ) -> None:
        """Emit reshape + optional slice for strided input parameters.

        For each strided param, reshapes ``(M, N)`` to ``(M, N/stride, stride)``
        and, when ``skip > 0``, slices off leading blocks so the remaining
        elements align with the output.
        """
        for param in params:
            buf_name = self._param_to_buf_name(param)
            if buf_name is None or buf_name not in self.strided_input_buffers:
                continue
            strides = self.strided_input_buffers[buf_name]
            info = self._get_buffer_info(buf_name)
            if info is None:
                continue
            _, buf_size, _, _, _ = info
            new_shape_parts: list[str] = []
            for d, (stride, _offset, _skip) in enumerate(strides):
                dim = self._safe_int(buf_size[d])
                if dim is None:
                    break
                if stride > 1:
                    new_shape_parts.append(str(dim // stride))
                    new_shape_parts.append(str(stride))
                else:
                    new_shape_parts.append(str(dim))
            else:
                code.writeline(
                    f"{param} = {param}.reshape({', '.join(new_shape_parts)})"
                )
                if any(skip > 0 for _, _, skip in strides):
                    slice_parts: list[str] = []
                    for stride, _offset, skip in strides:
                        if stride == 1:
                            slice_parts.append(":")
                        else:
                            slice_parts.append(f"{skip}:" if skip > 0 else ":")
                            slice_parts.append(":")
                    code.writeline(f"{param} = {param}[{', '.join(slice_parts)}]")