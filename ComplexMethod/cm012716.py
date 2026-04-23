def normalize_shapes(inputs, layout_or_out):
            new_inputs = list(inputs)
            if not is_mkldnn_wgt and isinstance(new_inputs[1], torch.Tensor):
                if has_free_symbols(view_size):
                    # If batch size B is dynamic, we need to set the batch size and possibly stride
                    assert not has_free_symbols(view_size[1:])
                    view_size[:] = V.graph.sizevars.guarding_hints_or_throw(view_size)
                    view_stride[:] = V.graph.sizevars.guarding_hints_or_throw(
                        view_stride
                    )
                # With the assumptation that W is the storage of unwrap view
                # thus view it back here
                new_inputs[1] = new_inputs[1].as_strided(
                    view_size, view_stride, view_offset
                )

            if not trans_w:
                return new_inputs, layout_or_out
            X = new_inputs[0]
            W = new_inputs[1]
            B = new_inputs[2] if has_bias else None
            W = transpose_w(W, trans_w)
            B = expand_bias(B, X)  # type:ignore[arg-type]
            new_inputs[1] = W
            if B is not None:
                new_inputs[2] = B
            return new_inputs, layout_or_out