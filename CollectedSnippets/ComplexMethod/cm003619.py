def preprocess(
        self,
        images: ImageInput,
        return_tensors: str | TensorType | None = "pt",
    ) -> BatchFeature:
        """
        Preprocess an image or batch of images.

        Args:
            images (`ImageInput`):
                Image to preprocess. Expects a single or batch of images
            return_tensors (`str` or `TensorType`, *optional*):
                The type of tensors to return.
        """
        if return_tensors != "pt":
            raise ValueError(f"return_tensors for TimmWrapperImageProcessor must be 'pt', but got {return_tensors}")

        if self._not_supports_tensor_input and isinstance(images, torch.Tensor):
            images = images.cpu().numpy()

        # If the input is a torch tensor, then no conversion is needed
        # Otherwise, we need to pass in a list of PIL images
        if isinstance(images, torch.Tensor):
            images = self.val_transforms(images)
            # Add batch dimension if a single image
            images = images.unsqueeze(0) if images.ndim == 3 else images
        else:
            images = make_flat_list_of_images(images)
            images = [to_pil_image(image) for image in images]
            images = torch.stack([self.val_transforms(image) for image in images])

        return BatchFeature({"pixel_values": images}, tensor_type=return_tensors)