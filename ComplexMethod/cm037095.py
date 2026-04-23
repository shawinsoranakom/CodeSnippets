def __call__(
        self, img: Image.Image
    ) -> tuple[Image.Image, list[Image.Image], list[bool]]:
        img_width, img_height = img.size
        new_img_width, new_img_height = self.get_image_size_for_padding(
            img_width, img_height
        )
        if new_img_width != img_width or new_img_height != img_height:
            img = self.square_pad(img)
            img_width, img_height = img.size

        new_img_width, new_img_height = self.get_image_size_for_preprocess(
            img_width, img_height
        )
        img = img.resize((new_img_width, new_img_height), Image.Resampling.BILINEAR)
        window_size = self.determine_window_size(
            max(new_img_height, new_img_width), min(new_img_height, new_img_width)
        )

        if window_size == 0 or not self.enable_patch:
            return img, [], []
        else:
            new_img_width, new_img_height = self.get_image_size_for_crop(
                new_img_width, new_img_height, window_size
            )
            if (new_img_width, new_img_height) != (img_width, img_height):
                img_for_crop = img.resize(
                    (new_img_width, new_img_height), Image.Resampling.BILINEAR
                )
            else:
                img_for_crop = img

            patches = []
            newlines = []
            center_list, (x_num, y_num) = self.slide_window(
                new_img_width,
                new_img_height,
                [(window_size, window_size)],
                [(window_size, window_size)],
            )
            for patch_id, center_lf_point in enumerate(center_list):
                x, y, patch_w, patch_h = center_lf_point
                big_patch = self.patch_crop(img_for_crop, y, x, patch_h, patch_w)
                patches.append(big_patch)
                if (patch_id + 1) % x_num == 0:
                    newlines.append(patch_id)

            if newlines and newlines[-1] == len(patches) - 1:
                newlines.pop()

            return (
                img,
                patches,
                [i in newlines for i in range(len(patches))],
            )