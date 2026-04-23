def _handle_argument(
        self,
        value: Any,
        is_write: bool,
        metadata_only: bool,
        name: str | None = None,
        is_output: bool = False,
    ) -> None:
        if isinstance(value, torch.Tensor) and value.is_cuda:
            # data_ptr() is preferred, but distinguish Tensors with null data_ptr()
            # otherwise two empty Tensors could incorrectly match as a conflict
            data_ptr = value.data_ptr() if value.data_ptr() else id(value)
            if is_write:
                self.dataptrs_written.add(data_ptr)
            elif not metadata_only:
                self.dataptrs_read.add(data_ptr)

            self.tensor_aliases.setdefault(data_ptr, [])
            if name is not None:
                self.tensor_aliases[data_ptr].append(name)
            if is_output:
                self.outputs.add(data_ptr)