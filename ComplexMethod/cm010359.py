def _collect_fake_inputs(inputs):
    from torch._subclasses.fake_tensor import FakeTensor

    # Get the example values of the inputs.
    inputs_fake: list[FakeTensor | torch.Tensor | int] = []
    for inp in inputs:
        if isinstance(inp, (torch.fx.proxy.Proxy, torch.fx.node.Node)):
            inp = inp.node if isinstance(inp, torch.fx.proxy.Proxy) else inp
            if hasattr(inp, "meta"):
                val = inp.meta["example_value"]
                if isinstance(val, torch.Tensor):
                    if torch._C._functorch.is_batchedtensor(
                        val
                    ) or torch._C._functorch.is_functionaltensor(val):
                        # This case is for batched or functional tensors
                        # Unwrap the tensors
                        while torch._C._functorch.is_batchedtensor(
                            val
                        ) or torch._C._functorch.is_functionaltensor(val):
                            val = torch._C._functorch.get_unwrapped(val)
                        if not isinstance(val, FakeTensor):
                            raise AssertionError(
                                f"Expected FakeTensor after unwrapping, got {type(val)}"
                            )
                        inputs_fake.append(val)
                    else:
                        # This is the standard case of a TensorVariable
                        if not isinstance(val, FakeTensor):
                            raise AssertionError(
                                f"Expected FakeTensor, got {type(val)}"
                            )
                        inputs_fake.append(val)
                else:
                    # This case is for SymInts and other non-Tensor elements
                    if isinstance(val, torch.Tensor):
                        raise AssertionError(f"Expected non-Tensor, got {type(val)}")
                    inputs_fake.append(val)
        else:
            # This case is for ints
            if not isinstance(inp, int):
                raise AssertionError(f"Expected int, got {type(inp)}")
            inputs_fake.append(inp)

    return inputs_fake