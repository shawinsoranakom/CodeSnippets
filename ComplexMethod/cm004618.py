def dynamic_preprocess(self, image, image_size, patch_size, mask_size, max_num=36, min_num=1):
        orig_height, orig_width = image.shape[-2:]

        w_crop_num = math.ceil(orig_width / float(image_size))
        h_crop_num = math.ceil(orig_height / float(image_size))
        if w_crop_num * h_crop_num > max_num:
            aspect_ratio = orig_width / orig_height

            # calculate the existing image aspect ratio
            target_ratios = {
                (i, j)
                for n in range(min_num, max_num + 1)
                for i in range(1, n + 1)
                for j in range(1, n + 1)
                if i * j <= max_num and i * j >= min_num
            }
            target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

            # find the closest aspect ratio to the target
            target_aspect_ratio = self.find_closest_aspect_ratio(
                aspect_ratio, target_ratios, orig_width, orig_height, image_size
            )

            # calculate the target width and height
            target_width = image_size * target_aspect_ratio[0]
            target_height = image_size * target_aspect_ratio[1]
        else:
            target_width = image_size * w_crop_num
            target_height = image_size * h_crop_num
            target_aspect_ratio = (w_crop_num, h_crop_num)

        # Calculate the ratio
        ratio_width = target_width / orig_width
        ratio_height = target_height / orig_height
        if ratio_width < ratio_height:
            new_size = (target_width, int(orig_height * ratio_width))
            padding_width = 0
            padding_height = target_height - int(orig_height * ratio_width)
        else:
            new_size = (int(orig_width * ratio_height), target_height)
            padding_width = target_width - int(orig_width * ratio_height)
            padding_height = 0

        attention_mask = torch.ones(
            (int(mask_size * target_aspect_ratio[1]), int(mask_size * target_aspect_ratio[0])),
            device=image.device,
        )
        if padding_width >= patch_size:
            attention_mask[:, -math.floor(padding_width / patch_size) :] = 0
        if padding_height >= patch_size:
            attention_mask[-math.floor(padding_height / patch_size) :, :] = 0

        if min(new_size[1], target_height) < 10 or min(new_size[0], target_width) < 10:
            raise ValueError(f"the aspect ratio is very extreme {new_size}")

        image = tvF.resize(image, [new_size[1], new_size[0]])
        resized_img = tvF.pad(image, [0, 0, padding_width, padding_height], fill=[255, 255, 255])

        return resized_img, attention_mask