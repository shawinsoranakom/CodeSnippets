def get_dtype(self, buffer_name: str) -> torch.dtype:
        if buffer_name in self.constants:
            return self.constants[buffer_name].dtype
        # For a mutation op we should return the dtype of the buffer being mutated
        if (
            hasattr(self.scheduler, "mutation_real_name")
            and buffer_name in self.scheduler.mutation_real_name
        ):
            mutated_buf = self.scheduler.mutation_real_name[buffer_name]
            if mutated_buf in self.name_to_buffer:
                return self.name_to_buffer[mutated_buf].get_dtype()
            if mutated_buf in self.graph_inputs:
                return self.graph_inputs[mutated_buf].get_dtype()
        if buffer_name in self.name_to_buffer:
            return self.name_to_buffer[buffer_name].get_dtype()
        if buffer_name in self.graph_inputs:
            return self.graph_inputs[buffer_name].get_dtype()
        m = re.match(r"(as_strided|reinterpret_tensor)\(([a-zA-Z0-9_]+),", buffer_name)
        if m:
            return self.get_dtype(m.group(1))
        raise KeyError(f"could not find {buffer_name}")