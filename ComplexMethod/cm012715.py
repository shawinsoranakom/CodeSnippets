def reorder_and_filter(inputs, layout_or_out):
            if has_bias:
                assert len(input_indices) >= 3
                # Assume the input order is [inp, x, w] and we reorder it to [x, w, inp]
                inp_idx = input_indices[0]
                x_idx = input_indices[1]
                w_idx = input_indices[2]
                return [
                    inputs[x_idx],
                    inputs[w_idx],
                    inputs[inp_idx],
                    *[inputs[idx] for idx in input_indices[3:]],
                ], layout_or_out
            elif len(inputs) >= len(input_indices):
                assert len(input_indices) >= 2
                return [inputs[idx] for idx in input_indices], layout_or_out
            else:
                # For when input is used for x and w, i.e. X@X.T or similar
                # Assumes the first input is the only input
                assert len(inputs) == 1
                return [inputs[0]] * len(input_indices), layout_or_out