def __call__(self, data):
        filename = data["filename"]
        img = Image.open(filename)
        try:
            if self.is_random_resize:
                img = self.random_resize(img)
            img = self.crop_margin(img.convert("RGB"))
            if "label" in data and self.is_random_crop:
                label = data["label"]
                equation_length = len(label)
                if equation_length < 256:
                    img = self.random_crop(img, crop_ratio=0.1)
                elif 256 < equation_length <= 512:
                    img = self.random_crop(img, crop_ratio=0.05)
                else:
                    img = self.random_crop(img, crop_ratio=0.03)
        except OSError:
            return
        if img.height == 0 or img.width == 0:
            return
        img = self.resize(img, min(self.input_size))
        img.thumbnail((self.input_size[1], self.input_size[0]))
        delta_width = self.input_size[1] - img.width
        delta_height = self.input_size[0] - img.height
        if self.is_random_padding:
            pad_width = np.random.randint(low=0, high=delta_width + 1)
            pad_height = np.random.randint(low=0, high=delta_height + 1)
        else:
            pad_width = delta_width // 2
            pad_height = delta_height // 2
        padding = (
            pad_width,
            pad_height,
            delta_width - pad_width,
            delta_height - pad_height,
        )

        data["image"] = np.array(ImageOps.expand(img, padding))
        return data