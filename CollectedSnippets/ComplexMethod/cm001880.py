def prepare_image_inputs(
        self,
        batch_size=None,
        min_resolution=None,
        max_resolution=None,
        num_channels=None,
        num_images=None,
        size_divisor=None,
        equal_resolution=False,
        numpify=False,
        torchify=False,
    ):
        """This function prepares a list of PIL images, or a list of numpy arrays if one specifies numpify=True,
        or a list of PyTorch tensors if one specifies torchify=True.

        One can specify whether the images are of the same resolution or not.
        """
        assert not (numpify and torchify), "You cannot specify both numpy and PyTorch tensors at the same time"

        batch_size = batch_size if batch_size is not None else self.batch_size
        min_resolution = min_resolution if min_resolution is not None else self.min_resolution
        max_resolution = max_resolution if max_resolution is not None else self.max_resolution
        num_channels = num_channels if num_channels is not None else self.num_channels
        num_images = num_images if num_images is not None else self.num_images

        images_list = []
        for i in range(batch_size):
            images = []
            for j in range(num_images):
                if equal_resolution:
                    width = height = max_resolution
                else:
                    # To avoid getting image width/height 0
                    if size_divisor is not None:
                        # If `size_divisor` is defined, the image needs to have width/size >= `size_divisor`
                        min_resolution = max(size_divisor, min_resolution)
                    width, height = np.random.choice(np.arange(min_resolution, max_resolution), 2)
                images.append(np.random.randint(255, size=(num_channels, width, height), dtype=np.uint8))
            images_list.append(images)

        if not numpify and not torchify:
            # PIL expects the channel dimension as last dimension
            images_list = [[Image.fromarray(np.moveaxis(image, 0, -1)) for image in images] for images in images_list]

        if torchify:
            images_list = [[torch.from_numpy(image) for image in images] for images in images_list]

        return images_list