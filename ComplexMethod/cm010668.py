def wrapper(*args):
            in_args: list[torch.Tensor] = []
            for i in range(len(in_vars)):
                if not isinstance(args[i], torch.Tensor):
                    raise RuntimeError("Expected Tensor argument")
                in_args.append(args[i])

            trace_inputs = _unflatten(in_args, in_desc)

            if self._return_inputs:
                ret_inputs.append(
                    tuple(x.clone(memory_format=torch.preserve_format) for x in args)
                )
            if self._return_inputs_states:
                inputs_states.append(_unflatten(in_args, in_desc))
            outs.append(self.inner(*trace_inputs))
            if self._return_inputs_states:
                inputs_states[0] = (inputs_states[0], trace_inputs)
            out_vars, _ = _flatten(outs)
            if len(out_vars) == 1:
                return out_vars[0]
            else:
                return tuple(out_vars)