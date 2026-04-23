def post_process_depth_estimation(
        self,
        outputs: "DepthProDepthEstimatorOutput",
        target_sizes: TensorType | list[tuple[int, int]] | None = None,
    ) -> list[dict[str, TensorType]]:
        """Post-processes the raw depth predictions from the model."""
        requires_backends(self, "torch")
        predicted_depth = outputs.predicted_depth
        fov = outputs.field_of_view
        batch_size = len(predicted_depth)
        if target_sizes is not None and batch_size != len(target_sizes):
            raise ValueError(
                "Make sure that you pass in as many fov values as the batch dimension of the predicted depth"
            )
        results = []
        fov = [None] * batch_size if fov is None else fov
        target_sizes = [None] * batch_size if target_sizes is None else target_sizes
        for depth, fov_value, target_size in zip(predicted_depth, fov, target_sizes):
            focal_length = None
            if target_size is not None:
                # scale image w.r.t fov
                if fov_value is not None:
                    width = target_size[1]
                    focal_length = 0.5 * width / torch.tan(0.5 * torch.deg2rad(fov_value))
                    depth = depth * width / focal_length
                depth = torch.nn.functional.interpolate(
                    # input should be (B, C, H, W)
                    input=depth.unsqueeze(0).unsqueeze(1),
                    size=target_size,
                    mode=pil_torch_interpolation_mapping[self.resample].value,
                ).squeeze()
            depth = 1.0 / torch.clamp(depth, min=1e-4, max=1e4)
            results.append(
                {
                    "predicted_depth": depth,
                    "field_of_view": fov_value,
                    "focal_length": focal_length,
                }
            )
        return results