def forward(
        self,
        inputs: torch.Tensor,
        pos: torch.Tensor | None = None,
        network_input_is_1d: bool = True,
        interpolate_pos_encoding: bool = False,
    ):
        if self.prep_type == "conv":
            # Convnet image featurization.
            # Downsamples spatially by a factor of 4
            inputs = self.convnet(inputs)

        elif self.prep_type == "conv1x1":
            # map inputs to self.out_channels
            inputs = self.convnet_1x1(inputs)

        elif self.prep_type == "pixels":
            # if requested, downsamples in the crudest way
            if inputs.ndim == 4:
                inputs = inputs[:: self.spatial_downsample, :: self.spatial_downsample]
            elif inputs.ndim == 5:
                inputs = inputs[
                    :, :: self.temporal_downsample, :, :: self.spatial_downsample, :: self.spatial_downsample
                ]
            else:
                raise ValueError("Unsupported data format for pixels.")

        elif self.prep_type == "patches":
            # Space2depth featurization.
            # Video: B x T x C x H x W
            inputs = space_to_depth(
                inputs, temporal_block_size=self.temporal_downsample, spatial_block_size=self.spatial_downsample
            )

            if inputs.ndim == 5 and inputs.shape[1] == 1:
                # for flow
                inputs = inputs.squeeze(dim=1)

            # Optionally apply conv layer.
            inputs = self.conv_after_patches(inputs)

        if self.prep_type != "patches":
            # move channels to last dimension, as the _build_network_inputs method below expects this
            if inputs.ndim == 4:
                inputs = inputs.permute(0, 2, 3, 1)
            elif inputs.ndim == 5:
                inputs = inputs.permute(0, 1, 3, 4, 2)
            else:
                raise ValueError("Unsupported data format for conv1x1.")

        inputs, inputs_without_pos = self._build_network_inputs(inputs, network_input_is_1d, interpolate_pos_encoding)
        modality_sizes = None  # Size for each modality, only needed for multimodal

        return inputs, modality_sizes, inputs_without_pos