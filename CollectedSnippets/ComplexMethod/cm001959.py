def prepare_image_inputs(self, equal_resolution=False, numpify=False, torchify=False):
        """Prepares a batch of images for testing"""
        if equal_resolution:
            image_inputs = [
                np.random.randint(
                    0, 256, (self.num_channels, self.max_resolution, self.max_resolution), dtype=np.uint8
                )
                for _ in range(self.batch_size)
            ]
        else:
            heights = [
                h - (h % 30) for h in np.random.randint(self.min_resolution, self.max_resolution, self.batch_size)
            ]
            widths = [
                w - (w % 30) for w in np.random.randint(self.min_resolution, self.max_resolution, self.batch_size)
            ]

            image_inputs = [
                np.random.randint(0, 256, (self.num_channels, height, width), dtype=np.uint8)
                for height, width in zip(heights, widths)
            ]

        if not numpify and not torchify:
            image_inputs = [Image.fromarray(np.moveaxis(img, 0, -1)) for img in image_inputs]

        if torchify:
            image_inputs = [torch.from_numpy(img) for img in image_inputs]

        return image_inputs