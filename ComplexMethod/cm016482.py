def control_merge(self, control, control_prev, output_dtype):
        out = {'input':[], 'middle':[], 'output': []}

        for key in control:
            control_output = control[key]
            applied_to = set()
            for i in range(len(control_output)):
                x = control_output[i]
                if x is not None:
                    if self.global_average_pooling:
                        x = torch.mean(x, dim=(2, 3), keepdim=True).repeat(1, 1, x.shape[2], x.shape[3])

                    if x not in applied_to: #memory saving strategy, allow shared tensors and only apply strength to shared tensors once
                        applied_to.add(x)
                        if self.strength_type == StrengthType.CONSTANT:
                            x *= self.strength
                        elif self.strength_type == StrengthType.LINEAR_UP:
                            x *= (self.strength ** float(len(control_output) - i))

                    if output_dtype is not None and x.dtype != output_dtype:
                        x = x.to(output_dtype)

                out[key].append(x)

        if control_prev is not None:
            for x in ['input', 'middle', 'output']:
                o = out[x]
                for i in range(len(control_prev[x])):
                    prev_val = control_prev[x][i]
                    if i >= len(o):
                        o.append(prev_val)
                    elif prev_val is not None:
                        if o[i] is None:
                            o[i] = prev_val
                        else:
                            if o[i].shape[0] < prev_val.shape[0]:
                                o[i] = prev_val + o[i]
                            else:
                                o[i] = prev_val + o[i] #TODO: change back to inplace add if shared tensors stop being an issue
        return out