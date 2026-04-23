def patchify_image(
        self, image: "np.ndarray | torch.Tensor", patch_size: SizeDict | None = None
    ) -> "np.ndarray | torch.Tensor":
        """
        Convert an image into a tensor of patches using numpy operations.
        Args:
            image (`np.ndarray` or `torch.Tensor`):
                Image to convert. Shape: [batch, channels, height, width] or [channels, height, width]
            patch_size (`SizeDict`, *optional*):
                Dictionary in the format `{"height": int, "width": int}` specifying the size of the patches.
        """
        requires_backends(self, ["torch"])
        import torch

        if patch_size is None:
            if isinstance(self.patch_size, SizeDict):
                patch_size = self.patch_size
            else:
                patch_size = SizeDict(**self.patch_size)
        patch_height, patch_width = patch_size.height, patch_size.width

        # Handle torch tensors by converting to numpy
        is_torch = isinstance(image, torch.Tensor)
        if is_torch:
            image_np = image.cpu().numpy()
            device = image.device
        else:
            image_np = image
            device = None

        # Handle batch dimension
        if len(image_np.shape) == 4:
            batch_size, channels, height, width = image_np.shape
        elif len(image_np.shape) == 3:
            batch_size = 1
            channels, height, width = image_np.shape
            image_np = image_np[np.newaxis, ...]
        else:
            raise ValueError(
                f"Expected image shape [batch, channels, height, width] or [channels, height, width], got {image_np.shape}"
            )

        # Extract patches using numpy operations to match torch unfold behavior exactly
        # Torch: unfold(2) -> unfold(3) -> view(b, c, -1, h, w) -> permute(0,2,3,4,1) -> reshape(b, -1, c*h*w)
        num_patches_h = height // patch_height
        num_patches_w = width // patch_width
        num_patches = num_patches_h * num_patches_w

        patches_list = []
        for b in range(batch_size):
            # Simulate torch unfold: extract patches along height, then width
            # After unfold(2) and unfold(3), shape is (channels, num_patches_h, patch_height, num_patches_w, patch_width)
            # After view: (channels, num_patches, patch_height, patch_width) where num_patches = num_patches_h * num_patches_w
            # After permute(0,2,3,4,1): (num_patches, patch_height, patch_width, channels)
            # After reshape: (num_patches, channels * patch_height * patch_width)

            # Reshape to extract patches: (channels, num_patches_h, patch_height, num_patches_w, patch_width)
            img_reshaped = image_np[b].reshape(channels, num_patches_h, patch_height, num_patches_w, patch_width)
            # Transpose to (channels, num_patches, patch_height, patch_width) where num_patches = num_patches_h * num_patches_w
            img_reshaped = img_reshaped.transpose(0, 1, 3, 2, 4).reshape(
                channels, num_patches, patch_height, patch_width
            )
            # Permute to (num_patches, patch_height, patch_width, channels) - matching torch permute(0,2,3,4,1)
            img_permuted = img_reshaped.transpose(1, 2, 3, 0)
            # Flatten to (num_patches, channels * patch_height * patch_width)
            patches = img_permuted.reshape(num_patches, channels * patch_height * patch_width)
            patches_list.append(patches)

        patches_array = np.stack(patches_list, axis=0) if batch_size > 1 else patches_list[0]

        # Convert back to torch if input was torch
        if is_torch:
            patches_array = torch.from_numpy(patches_array).to(device)

        return patches_array