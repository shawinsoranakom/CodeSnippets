def create_weights(
        self,
        layer: torch.nn.Module,
        output_size: int,
        input_size: int,
        output_partition_sizes: list[int],
        input_size_per_partition: int,
        params_dtype: torch.dtype,
        weight_loader: Callable,
        **kwargs,
    ):
        output_size_per_partition = sum(output_partition_sizes)

        mp_linear_kernel_config = MPLinearLayerConfig(
            full_weight_shape=(input_size, output_size),
            partition_weight_shape=(
                input_size_per_partition,
                output_size_per_partition,
            ),
            weight_type=self.quant_type,
            act_type=params_dtype,
            group_size=self.group_size,
            zero_points=not self.symmetric,
            has_g_idx=self.has_g_idx,
        )

        kernel_type = choose_mp_linear_kernel(mp_linear_kernel_config)

        if kernel_type.__name__ not in self._kernel_backends_being_used:
            logger.info("Using %s for CompressedTensorsWNA16", kernel_type.__name__)
            self._kernel_backends_being_used.add(kernel_type.__name__)

        if kernel_type is MarlinLinearKernel:
            input_dtype = get_marlin_input_dtype(self.layer_name)
            if input_dtype is not None:
                mp_linear_kernel_config.act_type = input_dtype

        # If group_size is -1, we are in channelwise case.
        group_size = self.group_size if self.group_size != -1 else input_size
        row_parallel = input_size != input_size_per_partition
        partition_scales = not marlin_repeat_scales_on_all_ranks(
            self.has_g_idx, self.group_size, row_parallel
        )

        scales_and_zp_size = input_size // group_size

        if partition_scales:
            assert input_size_per_partition % group_size == 0
            scales_and_zp_size = input_size_per_partition // group_size

        weight = PackedvLLMParameter(
            input_dim=1,
            output_dim=0,
            weight_loader=weight_loader,
            packed_factor=self.pack_factor,
            packed_dim=1,
            data=torch.empty(
                output_size_per_partition,
                input_size_per_partition // self.pack_factor,
                dtype=torch.int32,
            ),
        )

        weight_scale_args = {
            "weight_loader": weight_loader,
            "data": torch.empty(
                output_size_per_partition,
                scales_and_zp_size,
                dtype=params_dtype,
            ),
        }

        zeros_args = {
            "weight_loader": weight_loader,
            "data": torch.zeros(
                output_size_per_partition // self.pack_factor,
                scales_and_zp_size,
                dtype=torch.int32,
            ),
        }

        if not partition_scales:
            weight_scale = ChannelQuantScaleParameter(output_dim=0, **weight_scale_args)

            if not self.symmetric:
                qzeros = PackedColumnParameter(
                    output_dim=0,
                    packed_dim=0,
                    packed_factor=self.pack_factor,
                    **zeros_args,
                )
        else:
            weight_scale = GroupQuantScaleParameter(
                output_dim=0, input_dim=1, **weight_scale_args
            )
            if not self.symmetric:
                qzeros = PackedvLLMParameter(
                    input_dim=1,
                    output_dim=0,
                    packed_dim=0,
                    packed_factor=self.pack_factor,
                    **zeros_args,
                )

        # A 2D array defining the original shape of the weights
        # before packing
        weight_shape = BasevLLMParameter(
            data=torch.empty(2, dtype=torch.int64), weight_loader=weight_loader
        )

        layer.register_parameter("weight_packed", weight)
        layer.register_parameter("weight_scale", weight_scale)
        layer.register_parameter("weight_shape", weight_shape)

        if not self.symmetric:
            layer.register_parameter("weight_zero_point", qzeros)

        # group index (for activation reordering)
        if self.has_g_idx:
            weight_g_idx = RowvLLMParameter(
                data=torch.empty(
                    input_size_per_partition,
                    dtype=torch.int32,
                ),
                input_dim=0,
                weight_loader=weight_loader,
            )
            layer.register_parameter("weight_g_idx", weight_g_idx)

        self.kernel = kernel_type(
            mp_linear_kernel_config,
            w_q_param_name="weight_packed",
            w_s_param_name="weight_scale",
            w_zp_param_name="weight_zero_point",
            w_gidx_param_name="weight_g_idx",
        )