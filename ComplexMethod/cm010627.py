def backward(ctx: object, *grads: Tensor) -> tuple[Tensor, ...]:
                if len(grads) != len(static_grad_outputs):
                    raise AssertionError(
                        f"len(grads)={len(grads)} != len(static_grad_outputs)={len(static_grad_outputs)}"
                    )
                for g, grad in zip(static_grad_outputs, grads):
                    if g is not None:
                        # don't copy if autograd gods have been kind and the
                        # incoming grad is already in the right place
                        if g.data_ptr() != grad.data_ptr():
                            g.copy_(grad)
                bwd_graph.replay()

                # Input args that didn't require grad expect a None gradient.
                if not isinstance(static_grad_inputs, tuple):
                    raise AssertionError(
                        f"static_grad_inputs must be tuple, got {type(static_grad_inputs)}"
                    )
                return tuple(
                    # pyrefly: ignore [bad-argument-type]
                    b.detach() if b is not None else b
                    for b in static_grad_inputs
                )