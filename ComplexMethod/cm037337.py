def _postprocess_tensors(self) -> None:
        # Note: replace device tensors with cpu tensors
        def replace_tensor(obj: Any, cpu_attr_name: str, device_attr_name) -> None:
            cpu_tensor = getattr(obj, cpu_attr_name, None)
            device_tensor = getattr(obj, device_attr_name, None)
            if isinstance(cpu_tensor, torch.Tensor) and isinstance(
                device_tensor, torch.Tensor
            ):
                setattr(obj, device_attr_name, cpu_tensor)

        for v in vars(self).values():
            if isinstance(v, CpuGpuBuffer):
                v.gpu = v.cpu

        for k, v in vars(self.input_batch).items():
            if k.endswith("_cpu_tensor") and isinstance(v, torch.Tensor):
                replace_tensor(self.input_batch, k, k[:-11])

        for block_table in self.input_batch.block_table.block_tables:
            for v in vars(block_table).values():
                if isinstance(v, CpuGpuBuffer):
                    v.gpu = v.cpu