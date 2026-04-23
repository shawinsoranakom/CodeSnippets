def backward(ctx: object, *grads: Tensor) -> tuple[Tensor, ...]:
                if len(grads) != len(static_grad_outputs):
                    raise RuntimeError(
                        f"Expected {len(static_grad_outputs)} gradients but got {len(grads)}"
                    )
                for g, grad in zip(static_grad_outputs, grads):
                    if g is not None:
                        if g.data_ptr() != grad.data_ptr():
                            g.copy_(grad)
                bwd_graph.replay()

                if not isinstance(static_grad_inputs, tuple):
                    raise RuntimeError("static_grad_inputs must be a tuple")
                return tuple(
                    b.detach() if b is not None else b for b in static_grad_inputs
                )