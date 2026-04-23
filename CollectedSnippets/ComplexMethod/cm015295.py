def test_quantize_tensor_with_min_max(self):
        num_rows_list = [1, 2, 10, 100]
        num_cols_list = [4, 8, 16, 32, 64, 128]
        # Map of quantization bit rate to tuple of quantize function (with rowwise_min_max) and
        # quantize function (without rowwise_min_max)
        bit_rate_to_quant_fn: dict[
            int,
            tuple[
                OpOverloadPacket,
                OpOverloadPacket,
            ],
        ] = {
            8: (
                torch.ops.quantized.embedding_bag_byte_prepack_with_rowwise_min_max,
                torch.ops.quantized.embedding_bag_byte_prepack,
            ),
            4: (
                torch.ops.quantized.embedding_bag_4bit_prepack_with_rowwise_min_max,
                torch.ops.quantized.embedding_bag_4bit_prepack,
            ),
            2: (
                torch.ops.quantized.embedding_bag_2bit_prepack_with_rowwise_min_max,
                torch.ops.quantized.embedding_bag_2bit_prepack,
            ),
        }

        for quant_fn_with_rowwise_min_max, quant_fn in bit_rate_to_quant_fn.values():
            for torch_dtype in [torch.float16, torch.float32]:
                for num_rows, num_cols in itertools.product(num_rows_list, num_cols_list):
                    weight = torch.rand(num_rows, num_cols, dtype=torch_dtype)
                    rowwise_min_max = torch.stack(
                        [weight.min(dim=1).values, weight.max(dim=1).values], dim=1
                    )

                    # Perform the quantization with rowwise_min_max
                    weight_quantized = quant_fn_with_rowwise_min_max(
                        weight, rowwise_min_max
                    )
                    if weight_quantized.dtype != torch.uint8:
                        raise AssertionError(
                            f"Expected weight_quantized.dtype == torch.uint8, "
                            f"got {weight_quantized.dtype}"
                        )

                    # Confirm that the quantization is matching the one without rowwise_min_max
                    weight_quantized_no_rowwise_min_max = quant_fn(weight)
                    if not torch.equal(
                        weight_quantized, weight_quantized_no_rowwise_min_max
                    ):
                        raise AssertionError(
                            "weight_quantized does not equal "
                            "weight_quantized_no_rowwise_min_max"
                        )

                    # Confirtm that incorrect rowwise_min_max will result in different quantization output
                    incorrect_rowwise_min_max = torch.stack(
                        [weight.max(dim=1).values, weight.max(dim=1).values], dim=1
                    )
                    weight_incorrectly_quantized = quant_fn_with_rowwise_min_max(
                        weight, incorrect_rowwise_min_max
                    )
                    if weight_incorrectly_quantized.dtype != torch.uint8:
                        raise AssertionError(
                            f"Expected weight_incorrectly_quantized.dtype == torch.uint8, "
                            f"got {weight_incorrectly_quantized.dtype}"
                        )
                    if torch.equal(
                        weight_incorrectly_quantized, weight_quantized_no_rowwise_min_max
                    ):
                        raise AssertionError(
                            "weight_incorrectly_quantized should not equal "
                            "weight_quantized_no_rowwise_min_max"
                        )