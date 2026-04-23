def _validate_outputs_match(
    fake_output: Any,
    real_output: Any,
) -> None:
    """
    Validate that fake_fn and real_fn outputs have matching pytree structure,
    shapes, and dtypes.

    Raises:
        RuntimeError: If outputs don't match with detailed error message.
    """
    fake_flat, fake_spec = pytree.tree_flatten(fake_output)
    real_flat, real_spec = pytree.tree_flatten(real_output)

    if fake_spec != real_spec:
        raise RuntimeError(
            f"Output structure mismatch in @leaf_function decorator.\n"
            f"fake_impl returned structure: {fake_spec}\n"
            f"real_impl returned structure: {real_spec}\n"
            f"The fake_impl must return outputs with the same pytree structure as real_impl."
        )

    if len(fake_flat) != len(real_flat):
        raise RuntimeError(
            f"Output count mismatch in @leaf_function decorator.\n"
            f"fake_impl returned {len(fake_flat)} values\n"
            f"real_impl returned {len(real_flat)} values"
        )

    for i, (fake_val, real_val) in enumerate(zip(fake_flat, real_flat)):
        fake_is_tensor = isinstance(fake_val, torch.Tensor)
        real_is_tensor = isinstance(real_val, torch.Tensor)

        if fake_is_tensor != real_is_tensor:
            raise RuntimeError(
                f"Output type mismatch at position {i} in @leaf_function decorator.\n"
                f"fake_impl returned: {type(fake_val).__name__}\n"
                f"real_impl returned: {type(real_val).__name__}"
            )

        if fake_is_tensor:
            if fake_val.shape != real_val.shape:
                raise RuntimeError(
                    f"Shape mismatch at output position {i} in @leaf_function decorator.\n"
                    f"fake_impl output shape: {list(fake_val.shape)}\n"
                    f"real_impl output shape: {list(real_val.shape)}\n"
                    f"The fake_impl must produce tensors with the same shapes as real_impl."
                )

            if fake_val.dtype != real_val.dtype:
                raise RuntimeError(
                    f"Dtype mismatch at output position {i} in @leaf_function decorator.\n"
                    f"fake_impl output dtype: {fake_val.dtype}\n"
                    f"real_impl output dtype: {real_val.dtype}\n"
                    f"The fake_impl must produce tensors with the same dtypes as real_impl."
                )