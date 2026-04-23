def _preprocess(
        self,
        images: list[list[np.ndarray]],
        do_resize: bool,
        size: SizeDict,
        resample: PILImageResampling | None,
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_pad: bool,
        pad_size: SizeDict,
        constant_values: float | list[float],
        pad_mode: str,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_flip_channel_order: bool,
        return_tensors: str | TensorType | None = None,
        **kwargs,
    ) -> BatchFeature:
        """
        Preprocess videos using PIL backend.

        This method processes each video frame through the same pipeline as the original
        TVP image processor but uses PIL/NumPy operations.
        """
        processed_videos = []
        for video in images:
            processed_frames = []
            for frame in video:
                if do_resize:
                    frame = self.resize(frame, size, resample)
                if do_center_crop:
                    frame = self.center_crop(frame, crop_size)
                if do_rescale:
                    frame = self.rescale(frame, rescale_factor)
                if do_normalize:
                    frame = self.normalize(frame, image_mean, image_std)
                if do_pad:
                    pad_mode_enum = pad_mode if isinstance(pad_mode, PaddingMode) else PaddingMode(pad_mode)
                    frame = self.pad_image(frame, pad_size, constant_values, pad_mode_enum)
                if do_flip_channel_order:
                    frame = self._flip_channel_order(frame)
                processed_frames.append(frame)
            processed_videos.append(processed_frames)

        if return_tensors == "pt":
            from ...utils import is_torch_available

            if not is_torch_available():
                raise ImportError("PyTorch is required to return tensors")
            import torch

            processed_videos = [
                torch.stack([torch.from_numpy(frame.copy()) for frame in video], dim=0) for video in processed_videos
            ]
            processed_videos = torch.stack(processed_videos, dim=0)

        return BatchFeature(data={"pixel_values": processed_videos}, tensor_type=return_tensors)