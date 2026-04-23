def memory_required(self, input_shape, cond_shapes={}):
        input_shapes = [input_shape]
        for c in self.memory_usage_factor_conds:
            shape = cond_shapes.get(c, None)
            if shape is not None:
                if c in self.memory_usage_shape_process:
                    out = []
                    for s in shape:
                        out.append(self.memory_usage_shape_process[c](s))
                    shape = out

                if len(shape) > 0:
                    input_shapes += shape

        if comfy.model_management.xformers_enabled() or comfy.model_management.pytorch_attention_flash_attention():
            dtype = self.get_dtype_inference()
            #TODO: this needs to be tweaked
            area = sum(map(lambda input_shape: input_shape[0] * math.prod(input_shape[2:]), input_shapes))
            return (area * comfy.model_management.dtype_size(dtype) * 0.01 * self.memory_usage_factor) * (1024 * 1024)
        else:
            #TODO: this formula might be too aggressive since I tweaked the sub-quad and split algorithms to use less memory.
            area = sum(map(lambda input_shape: input_shape[0] * math.prod(input_shape[2:]), input_shapes))
            return (area * 0.15 * self.memory_usage_factor) * (1024 * 1024)