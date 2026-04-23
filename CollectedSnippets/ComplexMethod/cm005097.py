def post_process_depth_estimation(
        self,
        outputs: "ZoeDepthDepthEstimatorOutput",
        source_sizes: TensorType | list[tuple[int, int]] | None | None = None,
        target_sizes: TensorType | list[tuple[int, int]] | None | None = None,
        outputs_flipped: Union["ZoeDepthDepthEstimatorOutput", None] | None = None,
        do_remove_padding: bool | None | None = None,
    ) -> list[dict[str, TensorType]]:
        """
        Converts the raw output of [`ZoeDepthDepthEstimatorOutput`] into final depth predictions and depth PIL images.
        Only supports PyTorch.

        Args:
            outputs ([`ZoeDepthDepthEstimatorOutput`]):
                Raw outputs of the model.
            source_sizes (`TensorType` or `list[tuple[int, int]]`, *optional*):
                Tensor of shape `(batch_size, 2)` or list of tuples (`tuple[int, int]`) containing the source size
                (height, width) of each image in the batch before preprocessing. This argument should be dealt as
                "required" unless the user passes `do_remove_padding=False` as input to this function.
            target_sizes (`TensorType` or `list[tuple[int, int]]`, *optional*):
                Tensor of shape `(batch_size, 2)` or list of tuples (`tuple[int, int]`) containing the target size
                (height, width) of each image in the batch. If left to None, predictions will not be resized.
            outputs_flipped ([`ZoeDepthDepthEstimatorOutput`], *optional*):
                Raw outputs of the model from flipped input (averaged out in the end).
            do_remove_padding (`bool`, *optional*):
                By default ZoeDepth adds padding equal to `int(√(height / 2) * 3)` (and similarly for width) to fix the
                boundary artifacts in the output depth map, so we need remove this padding during post_processing. The
                parameter exists here in case the user changed the image preprocessing to not include padding.

        Returns:
            `list[dict[str, TensorType]]`: A list of dictionaries of tensors representing the processed depth
            predictions.
        """
        requires_backends(self, "torch")

        predicted_depth = outputs.predicted_depth

        if (outputs_flipped is not None) and (predicted_depth.shape != outputs_flipped.predicted_depth.shape):
            raise ValueError("Make sure that `outputs` and `outputs_flipped` have the same shape")

        if (target_sizes is not None) and (len(predicted_depth) != len(target_sizes)):
            raise ValueError(
                "Make sure that you pass in as many target sizes as the batch dimension of the predicted depth"
            )

        if do_remove_padding is None:
            do_remove_padding = self.do_pad

        if source_sizes is None and do_remove_padding:
            raise ValueError(
                "Either `source_sizes` should be passed in, or `do_remove_padding` should be set to False"
            )

        if (source_sizes is not None) and (len(predicted_depth) != len(source_sizes)):
            raise ValueError(
                "Make sure that you pass in as many source image sizes as the batch dimension of the logits"
            )

        if outputs_flipped is not None:
            predicted_depth = (predicted_depth + torch.flip(outputs_flipped.predicted_depth, dims=[-1])) / 2

        predicted_depth = predicted_depth.unsqueeze(1)

        # Zoe Depth model adds padding around the images to fix the boundary artifacts in the output depth map
        # The padding length is `int(np.sqrt(img_h/2) * fh)` for the height and similar for the width
        # fh (and fw respectively) are equal to '3' by default
        # Check [here](https://github.com/isl-org/ZoeDepth/blob/edb6daf45458569e24f50250ef1ed08c015f17a7/zoedepth/models/depth_model.py#L57)
        # for the original implementation.
        # In this section, we remove this padding to get the final depth image and depth prediction
        padding_factor_h = padding_factor_w = 3

        results = []
        target_sizes = [None] * len(predicted_depth) if target_sizes is None else target_sizes
        source_sizes = [None] * len(predicted_depth) if source_sizes is None else source_sizes
        for depth, target_size, source_size in zip(predicted_depth, target_sizes, source_sizes):
            # depth.shape = [1, H, W]
            if source_size is not None:
                pad_h = pad_w = 0

                if do_remove_padding:
                    pad_h = int(np.sqrt(source_size[0] / 2) * padding_factor_h)
                    pad_w = int(np.sqrt(source_size[1] / 2) * padding_factor_w)

                depth = tvF.resize(
                    depth,
                    size=[source_size[0] + 2 * pad_h, source_size[1] + 2 * pad_w],
                    interpolation=tvF.InterpolationMode.BICUBIC,
                    antialias=False,
                )

                if pad_h > 0:
                    depth = depth[:, pad_h:-pad_h, :]
                if pad_w > 0:
                    depth = depth[:, :, pad_w:-pad_w]

            if target_size is not None:
                target_size = [target_size[0], target_size[1]]
                depth = tvF.resize(
                    depth,
                    size=target_size,
                    interpolation=tvF.InterpolationMode.BICUBIC,
                    antialias=False,
                )
            depth = depth.squeeze(0)
            # depth.shape = [H, W]
            results.append({"predicted_depth": depth})

        return results