def _register_qlinear_weight_prepack():
    # 6 Linear related patterns will be matched based on the dtype, input dimension size and input contiguous.
    # Then convert the pattern into a QLinear node with int8_fp32/bf16.
    # Case 1: int8-mixed-fp32, input dim size is 2
    # Case 2: int8-mixed-fp32, input dim size exceeds 2 and contiguous
    # Case 3: int8-mixed-bf16, input dim size is 2
    # Case 4: int8-mixed-bf16, input dim size exceeds 2 and contiguous

    #   + - - - - | - - - - - - | - - - - - +
    #   |    dq_per_tensor  dq_per_channel  |
    #   |         |              |          |
    #   |    OPT(to_bf16)    OPT(to_bf16)   |
    #   |         |              |          |
    #   |     OPT(reshape)   permute        |
    #   |            \        /             |
    #   |             addmm/mm              |
    #   |                |                  |
    #   |           OPT(reshape)            |

    # Case 5: int8-mixed-fp32, input dim size exceeds 2 and not contiguous
    # Case 6: int8-mixed-bf16, input dim size exceeds 2 and not contiguous

    #   + - - - - | - - - - - - | - - - - - +
    #   |    dq_per_tensor  dq_per_channel  |
    #   |         |              |          |
    #   |    OPT(to_bf16)    OPT(to_bf16)   |
    #   |         |              |          |
    #   |       expand       permute        |
    #   |          \             |          |
    #   |                    expand         |
    #   |                    /              |
    #   |               bmm                 |
    #   |                |                  |
    #   |            OPT(add)               |

    linear_weight_prepack_cases = itertools.product(
        [torch.float32, torch.bfloat16], [True, False], [True, False], [True, False]
    )

    # Step 1: register patterns from mm and addmm
    for (
        dtype,
        input_dim_exceeds_two,
        is_tensor_overload,
        with_dtype_convert,
    ) in linear_weight_prepack_cases:
        if dtype == torch.float32 and with_dtype_convert:
            continue
        weight_prepack_patterns = _generate_qlinear_weight_prepack_patterns(
            dtype,
            input_dim_exceeds_two,
            is_tensor_overload=is_tensor_overload,
            with_dtype_convert=with_dtype_convert,
        )
        for weight_prepack_pattern in weight_prepack_patterns:
            # Register to pass_number 1, so we can do dequant promotion in pass_number 0.
            _register_qlinear_weight_prepack_pass(
                weight_prepack_pattern,
                pass_number=1,
                dtype=dtype,
                input_dim_exceeds_two=input_dim_exceeds_two,
                with_dtype_convert=with_dtype_convert,
            )

    # Step 2: register patterns from bmm
    # Linear might be decomposed into bmm when input dim exceeds 2 and not contiguous
    # refer to:
    # https://github.com/pytorch/pytorch/blob/80c07df659362a95da7cd4f3ec367abfdace38c4/torch/_decomp/decompositions.py#L3965-L3968
    # in this case, we can convert it back to qlinear
    for (
        dtype,
        with_bias,
        is_tensor_overload,
        with_dtype_convert,
    ) in itertools.product(
        [torch.float32, torch.bfloat16], [True, False], [True, False], [True, False]
    ):
        if dtype == torch.float32 and with_dtype_convert:
            continue
        bmm_pattern = _generate_qlinear_weight_prepack_patterns(
            dtype=dtype,
            input_dim_exceeds_two=True,
            input_contiguous=False,
            with_bias=with_bias,
            is_tensor_overload=is_tensor_overload,
            with_dtype_convert=with_dtype_convert,
        )
        _register_qlinear_weight_prepack_pass(
            bmm_pattern,
            pass_number=1
            if with_bias
            else 2,  # if with_bias, there is an output add, so we should try to match it firstly
            dtype=dtype,
            input_dim_exceeds_two=True,
            input_contiguous=False,
            with_dtype_convert=with_dtype_convert,
        )