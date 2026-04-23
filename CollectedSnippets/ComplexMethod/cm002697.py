def normalize(self, image, mean, std, rescale=False):
        """
        Normalizes `image` with `mean` and `std`. Note that this will trigger a conversion of `image` to a NumPy array
        if it's a PIL Image.

        Args:
            image (`PIL.Image.Image` or `np.ndarray` or `torch.Tensor`):
                The image to normalize.
            mean (`list[float]` or `np.ndarray` or `torch.Tensor`):
                The mean (per channel) to use for normalization.
            std (`list[float]` or `np.ndarray` or `torch.Tensor`):
                The standard deviation (per channel) to use for normalization.
            rescale (`bool`, *optional*, defaults to `False`):
                Whether or not to rescale the image to be between 0 and 1. If a PIL image is provided, scaling will
                happen automatically.
        """
        self._ensure_format_supported(image)

        if isinstance(image, PIL.Image.Image):
            image = self.to_numpy_array(image, rescale=True)
        # If the input image is a PIL image, it automatically gets rescaled. If it's another
        # type it may need rescaling.
        elif rescale:
            if isinstance(image, np.ndarray):
                image = self.rescale(image.astype(np.float32), 1 / 255.0)
            elif is_torch_tensor(image):
                image = self.rescale(image.float(), 1 / 255.0)

        if isinstance(image, np.ndarray):
            if not isinstance(mean, np.ndarray):
                mean = np.array(mean).astype(image.dtype)
            if not isinstance(std, np.ndarray):
                std = np.array(std).astype(image.dtype)
        elif is_torch_tensor(image):
            import torch

            if not isinstance(mean, torch.Tensor):
                if isinstance(mean, np.ndarray):
                    mean = torch.from_numpy(mean)
                else:
                    mean = torch.tensor(mean)
            if not isinstance(std, torch.Tensor):
                if isinstance(std, np.ndarray):
                    std = torch.from_numpy(std)
                else:
                    std = torch.tensor(std)

        if image.ndim == 3 and image.shape[0] in [1, 3]:
            return (image - mean[:, None, None]) / std[:, None, None]
        else:
            return (image - mean) / std