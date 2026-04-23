def postprocess(
        self,
        images: ImageInput,
        do_rescale: bool | None = None,
        rescale_factor: float | None = None,
        do_normalize: bool | None = None,
        image_mean: list[float] | None = None,
        image_std: list[float] | None = None,
        return_tensors: str | None = None,
    ) -> "torch.Tensor":
        do_rescale = do_rescale if do_rescale is not None else self.do_rescale
        rescale_factor = 1.0 / self.rescale_factor if rescale_factor is None else rescale_factor
        do_normalize = do_normalize if do_normalize is not None else self.do_normalize
        image_mean = image_mean if image_mean is not None else self.image_mean
        image_std = image_std if image_std is not None else self.image_std
        image_mean = tuple(-rescale_factor * mean / std for mean, std in zip(image_mean, image_std))
        image_std = tuple(1 / std for std in image_std)

        images = self.preprocess(
            images,
            do_rescale=do_rescale,
            rescale_factor=rescale_factor,
            do_normalize=do_normalize,
            image_mean=image_mean,
            image_std=image_std,
            do_resize=False,
            do_pad=False,
            return_tensors=return_tensors,
        ).pixel_values
        if do_rescale:
            images = [image.clip(0, 255).to(torch.uint8) for image in images]

        if do_normalize and do_rescale and return_tensors == "PIL.Image.Image":
            images = [tvF.to_pil_image(image) for image in images]

        return_tensors = return_tensors if return_tensors != "PIL.Image.Image" else None
        images = torch.stack(images, dim=0) if return_tensors == "pt" else images

        return BatchFeature(data={"pixel_values": images}, tensor_type=return_tensors)