def fn_to_trace(*args: Any) -> Any:
            nonlocal num_fw_outs
            out = functional_call(*args)
            if output_loss_index is None:
                raise RuntimeError(
                    """\
If trace_joint=Trueit is required that one of your forward outputs must be a scalar loss.
You must specify the which (index) output is the loss with output_loss_index."""
                )
            if isinstance(out, (torch.Tensor)):
                out = (out,)
            if not isinstance(out, (tuple, list)):
                raise RuntimeError(
                    f"Expected forward output to be either a tensor or a list/tuple of tensors. found {type(out)}"
                )

            for i, o in enumerate(out):
                # We only want to create a backward graph w.r.t. the loss that the user passed in.
                # This implies that every other output should not require gradients.
                # Instead of making this an error (and forcing the user to detach all other outputs
                # of their forward),
                # we'll automatically detach them here.
                if o.requires_grad and i != output_loss_index:
                    raise RuntimeError(
                        f"""\
Found an output of the forward that requires gradients, that was not the scalar loss.
We require all outputs to the forward that are not the scalar loss to not require gradient,
because we will only compute a backward graph against the scalar loss.
You can fix this by calling .detach() on each of your forward outputs that is not the loss.
You specified that output index {output_loss_index} is the loss, but we found that
the output at index {i} requires gradients."""
                    )
            out_loss = out[output_loss_index]
            num_fw_outs = len(out)
            if not out_loss.requires_grad:
                raise RuntimeError(
                    f"""\
The output at index {output_loss_index} was marked as the loss, but it does not require gradients"""
                )
            if out_loss.numel() != 1:
                raise RuntimeError(
                    f"""\
We require the output marked as the loss (at index {output_loss_index}) to be a scalar, but it has shape {out_loss.shape}"""
                )
            return out