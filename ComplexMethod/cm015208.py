def _vmap_test(
    self,
    op,
    inputs,
    in_dims=0,
    out_dims=0,
    check_view=False,
    check_propagates_grad=True,
):
    result = vmap(op, in_dims, out_dims)(*inputs)
    are_nested = [t.is_nested for t in pytree.tree_leaves(result)]
    reference_result = reference_vmap(
        op, inputs, in_dims, out_dims, return_nt=any(are_nested)
    )
    self.assertEqual(result, reference_result)
    op_has_single_return = not isinstance(result, tuple)

    if check_view:
        result_as_tuple = (result,) if op_has_single_return else result
        for output in result_as_tuple:
            input0_base = inputs[0] if inputs[0]._base is None else inputs[0]._base
            self.assertTrue(
                output._base is input0_base,
                msg="result was not a view of the first input!",
            )

    if not check_propagates_grad:
        return
    # Assuming input[0] is a floating-point tensor. Check if the vmap
    # operation propagates the requires_grad flag to the zeroth output.
    # Some vmap operators are implemented in a way that assumes that
    # they are composite with respect to autograd. If the operator ever is
    # changed to not be composite with respect to autograd, then the
    # following check should fail.
    inputs_clone = list(inputs)
    inputs_clone[0] = inputs[0].clone().requires_grad_()
    result = vmap(op, in_dims, out_dims)(*inputs_clone)
    result_as_tuple = (result,) if op_has_single_return else result
    self.assertTrue(result[0].requires_grad)