def make_inplace(self, input_name: str, output_name: str) -> None:
        if input_name in V.graph.unaligned_buffers:
            V.graph.unaligned_buffers.add(output_name)
        assert output_name not in self.inplace_buffers, output_name
        if input_name in self.inplace_buffers:
            buf = self.inplace_buffers[input_name]
            assert not isinstance(buf, RemovedArg)
            buf.other_names.append(output_name)
            self.inplace_buffers[output_name] = buf
        else:
            alive_buffers = [
                val
                for val in self.inplace_buffers.values()
                if not isinstance(val, RemovedArg)
            ]
            removed_buffers = [
                val
                for val in self.inplace_buffers.values()
                if isinstance(val, RemovedArg)
            ]
            inplace_buffer_idx = len(unique(alive_buffers)) + len(removed_buffers)
            buf = InplacedBuffer(
                f"in_out_ptr{inplace_buffer_idx}",
                [input_name, output_name],
            )
            self.inplace_buffers[input_name] = buf
            self.inplace_buffers[output_name] = buf