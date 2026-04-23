def update_zero_dim_cpu_tensor(self) -> None:
        for node in self.nodes:
            if node.is_gpu():
                for read in node.read_writes.reads:
                    buffer = V.graph.name_to_buffer.get(read.name)
                    if (
                        buffer
                        and get_device_type(buffer) == "cpu"
                        and not isinstance(
                            buffer.layout, (NoneLayout, MultiOutputLayout)
                        )
                        and buffer.get_size() == []
                    ):
                        V.graph.zero_dim_cpu_tensor_list.add(read.name)