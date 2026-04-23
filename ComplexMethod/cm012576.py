def generate_other_buffer(self, buf_list, start_offset, len_attr, kernel_args):
        kernel_input_name_to_buffer_name = {
            key: value if isinstance(value, sympy.Symbol) else value.get_name()
            for key, value in self.kernel_input_name_to_buffer.items()
        }

        def get_arg(name):
            return kernel_input_name_to_buffer_name.get(name)

        def get_arg_name(name):
            if isinstance(get_arg(name), sympy.Symbol):
                return kernel_args.sizevars.get(get_arg(name))
            return kernel_args.input_buffers.get(get_arg(name))

        if not self.has_other_buffer:
            return ""

        if start_offset == -1:
            start_offset = self.len_score_other

        length = getattr(self, len_attr)
        for i in range(length):
            pointer = f"in_ptr{self.other_buf_start_idx + start_offset + i}"
            buffer_key = f"{buf_list}_{i}"
            if pointer not in self.other_ptr_data:
                self.other_ptr_data[pointer] = (
                    get_arg_name(buffer_key),
                    get_arg(buffer_key),
                )

        return "\n".join(
            f"auto {ptr} = {name};" for ptr, (name, _) in self.other_ptr_data.items()
        )