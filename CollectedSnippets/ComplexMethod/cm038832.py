def forward(
        self, input_: torch.Tensor
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor | None]:
        """Forward of RowParallelLinear

        Args:
            input_: tensor whose last dimension is `input_size`. If
                    `input_is_parallel` is set, then the last dimension
                    is `input_size // tp_size`.

        Returns:
            - output
            - bias
        """
        # set up backprop all-reduce.
        if self.base_layer.input_is_parallel:
            input_parallel = input_
        else:
            # TODO: simplify code below
            split_input = split_tensor_along_last_dim(
                input_, num_partitions=self.tp_size
            )
            input_parallel = split_input[self.tp_rank].contiguous()

        # Matrix multiply.
        bias_ = (
            None
            if (self.tp_rank > 0 or self.base_layer.skip_bias_add)
            else self.base_layer.bias
        )
        output_parallel = self.apply(input_parallel, bias_)
        if self.base_layer.reduce_results and self.tp_size > 1:
            output = tensor_model_parallel_all_reduce(output_parallel)
        else:
            output = output_parallel

        output_bias = self.base_layer.bias if self.base_layer.skip_bias_add else None
        if not self.base_layer.return_bias:
            return output

        return output, output_bias