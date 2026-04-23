def module_inputs_torch_nn_ConvNd(module_info, device, dtype, requires_grad, training, **kwargs):
    N = kwargs['N']
    lazy = kwargs.get('lazy', False)
    transposed = kwargs.get('transposed', False)
    make_input = partial(make_tensor, device=device, dtype=dtype, requires_grad=requires_grad)
    conv_kwargs_list = [{}] if transposed else [{}, {'padding': 'same'}]
    kernel_size, C_in, C_out = 3, 4, 5
    input_no_batch_shape = (C_in,) + tuple(i + 3 for i in range(N))
    input_batch_shape = (2,) + input_no_batch_shape
    return [
        ModuleInput(constructor_input=(FunctionInput(C_out, kernel_size, **conv_kwargs) if lazy else
                                       FunctionInput(C_in, C_out, kernel_size, **conv_kwargs)),
                    forward_input=FunctionInput(make_input(
                        input_batch_shape if with_batch else input_no_batch_shape)),
                    desc=('' if with_batch else 'no_batch_dim'),
                    reference_fn=(None if with_batch else no_batch_dim_reference_fn))
        for with_batch, conv_kwargs in itertools.product([True, False], conv_kwargs_list)
    ]