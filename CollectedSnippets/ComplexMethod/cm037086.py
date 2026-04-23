def tokenize_with_images(
        self,
        conversation: str,
        images: list[Image.Image],
        bos: bool = True,
        eos: bool = True,
        cropping: bool = True,
    ):
        """Tokenize text with <image> tags."""
        assert conversation.count(self.image_token) == len(images)
        text_splits = conversation.split(self.image_token)
        images_list, images_seq_mask, images_spatial_crop = [], [], []
        num_image_tokens = []
        tokenized_str = []
        for text_sep, image in zip(text_splits, images):
            """encode text_sep"""
            tokenized_sep = self.encode(text_sep, bos=False, eos=False)
            tokenized_str += tokenized_sep
            images_seq_mask += [False] * len(tokenized_sep)

            """select best resolution for anyres"""
            if cropping:
                best_width, best_height = self.select_best_resolution(image.size)
            else:
                best_width, best_height = self.image_size, self.image_size

            """process the global view"""
            global_view = ImageOps.pad(
                image,
                (self.image_size, self.image_size),
                color=tuple(int(x * 255) for x in self.image_transform.mean),
            )
            images_list.append(self.image_transform(global_view))

            """process the local views"""
            local_view = ImageOps.pad(
                image,
                (best_width, best_height),
                color=tuple(int(x * 255) for x in self.image_transform.mean),
            )
            for i in range(0, best_height, self.image_size):
                for j in range(0, best_width, self.image_size):
                    images_list.append(
                        self.image_transform(
                            local_view.crop(
                                (j, i, j + self.image_size, i + self.image_size)
                            )
                        )
                    )

            """record height / width crop num"""
            num_width_tiles, num_height_tiles = (
                best_width // self.image_size,
                best_height // self.image_size,
            )
            images_spatial_crop.append([num_width_tiles, num_height_tiles])

            """add image tokens"""
            h = w = math.ceil(
                (self.image_size // self.patch_size) / self.downsample_ratio
            )
            # global views tokens h * (w + 1), 1 is for line separator
            tokenized_image = [self.image_token_id] * h * (w + 1)
            # add a separator between global and local views
            tokenized_image += [self.image_token_id]
            # local views tokens, (num_height_tiles * h) * (num_width_tiles * w + 1)
            tokenized_image += (
                [self.image_token_id]
                * (num_height_tiles * h)
                * (num_width_tiles * w + 1)
            )

            tokenized_str += tokenized_image
            images_seq_mask += [True] * len(tokenized_image)
            num_image_tokens.append(len(tokenized_image))

        """process the last text split"""
        tokenized_sep = self.encode(text_splits[-1], bos=False, eos=False)
        tokenized_str += tokenized_sep
        images_seq_mask += [False] * len(tokenized_sep)

        """add the bos and eos tokens"""
        if bos:
            tokenized_str = [self.bos_id] + tokenized_str
            images_seq_mask = [False] + images_seq_mask
        if eos:
            tokenized_str = tokenized_str + [self.eos_id]
            images_seq_mask = images_seq_mask + [False]

        assert len(tokenized_str) == len(images_seq_mask), (
            f"tokenize_with_images func: tokenized_str's length {len(tokenized_str)} is not equal to imags_seq_mask's length {len(images_seq_mask)}"
        )

        return (
            tokenized_str,
            images_list,
            images_seq_mask,
            images_spatial_crop,
            num_image_tokens,
        )