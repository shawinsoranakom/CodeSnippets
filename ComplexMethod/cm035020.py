def __call__(self, data):
        input_size = 512
        im = data["image"]
        text_polys = data["polys"]
        text_tags = data["ignore_tags"]
        text_strs = data["texts"]
        h, w, _ = im.shape
        text_polys, text_tags, hv_tags = self.check_and_validate_polys(
            text_polys, text_tags, (h, w)
        )
        if text_polys.shape[0] <= 0:
            return None
        # set aspect ratio and keep area fix
        asp_scales = np.arange(1.0, 1.55, 0.1)
        asp_scale = np.random.choice(asp_scales)
        if np.random.rand() < 0.5:
            asp_scale = 1.0 / asp_scale
        asp_scale = math.sqrt(asp_scale)

        asp_wx = asp_scale
        asp_hy = 1.0 / asp_scale
        im = cv2.resize(im, dsize=None, fx=asp_wx, fy=asp_hy)
        text_polys[:, :, 0] *= asp_wx
        text_polys[:, :, 1] *= asp_hy

        if self.use_resize is True:
            ori_h, ori_w, _ = im.shape
            if max(ori_h, ori_w) < 200:
                ratio = 200 / max(ori_h, ori_w)
                im = cv2.resize(im, (int(ori_w * ratio), int(ori_h * ratio)))
                text_polys[:, :, 0] *= ratio
                text_polys[:, :, 1] *= ratio

            if max(ori_h, ori_w) > 512:
                ratio = 512 / max(ori_h, ori_w)
                im = cv2.resize(im, (int(ori_w * ratio), int(ori_h * ratio)))
                text_polys[:, :, 0] *= ratio
                text_polys[:, :, 1] *= ratio
        elif self.use_random_crop is True:
            h, w, _ = im.shape
            if max(h, w) > 2048:
                rd_scale = 2048.0 / max(h, w)
                im = cv2.resize(im, dsize=None, fx=rd_scale, fy=rd_scale)
                text_polys *= rd_scale
            h, w, _ = im.shape
            if min(h, w) < 16:
                return None

            # no background
            im, text_polys, text_tags, hv_tags, text_strs = self.crop_area(
                im, text_polys, text_tags, hv_tags, text_strs, crop_background=False
            )

        if text_polys.shape[0] == 0:
            return None
        # continue for all ignore case
        if np.sum((text_tags * 1.0)) >= text_tags.size:
            return None
        new_h, new_w, _ = im.shape
        if (new_h is None) or (new_w is None):
            return None
        # resize image
        std_ratio = float(input_size) / max(new_w, new_h)
        rand_scales = np.array(
            [0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.0, 1.0, 1.0, 1.0]
        )
        rz_scale = std_ratio * np.random.choice(rand_scales)
        im = cv2.resize(im, dsize=None, fx=rz_scale, fy=rz_scale)
        text_polys[:, :, 0] *= rz_scale
        text_polys[:, :, 1] *= rz_scale

        # add gaussian blur
        if np.random.rand() < 0.1 * 0.5:
            ks = np.random.permutation(5)[0] + 1
            ks = int(ks / 2) * 2 + 1
            im = cv2.GaussianBlur(im, ksize=(ks, ks), sigmaX=0, sigmaY=0)
        # add brighter
        if np.random.rand() < 0.1 * 0.5:
            im = im * (1.0 + np.random.rand() * 0.5)
            im = np.clip(im, 0.0, 255.0)
        # add darker
        if np.random.rand() < 0.1 * 0.5:
            im = im * (1.0 - np.random.rand() * 0.5)
            im = np.clip(im, 0.0, 255.0)

        # Padding the im to [input_size, input_size]
        new_h, new_w, _ = im.shape
        if min(new_w, new_h) < input_size * 0.5:
            return None
        im_padded = np.ones((input_size, input_size, 3), dtype=np.float32)
        im_padded[:, :, 2] = 0.485 * 255
        im_padded[:, :, 1] = 0.456 * 255
        im_padded[:, :, 0] = 0.406 * 255

        # Random the start position
        del_h = input_size - new_h
        del_w = input_size - new_w
        sh, sw = 0, 0
        if del_h > 1:
            sh = int(np.random.rand() * del_h)
        if del_w > 1:
            sw = int(np.random.rand() * del_w)

        # Padding
        im_padded[sh : sh + new_h, sw : sw + new_w, :] = im.copy()
        text_polys[:, :, 0] += sw
        text_polys[:, :, 1] += sh

        (
            score_map,
            score_label_map,
            border_map,
            direction_map,
            training_mask,
            pos_list,
            pos_mask,
            label_list,
            score_label_map_text_label,
        ) = self.generate_tcl_ctc_label(
            input_size, input_size, text_polys, text_tags, text_strs, 0.25
        )
        if len(label_list) <= 0:  # eliminate negative samples
            return None
        pos_list_temp = np.zeros([64, 3])
        pos_mask_temp = np.zeros([64, 1])
        label_list_temp = np.zeros([self.max_text_length, 1]) + self.pad_num

        for i, label in enumerate(label_list):
            n = len(label)
            if n > self.max_text_length:
                label_list[i] = label[: self.max_text_length]
                continue
            while n < self.max_text_length:
                label.append([self.pad_num])
                n += 1

        for i in range(len(label_list)):
            label_list[i] = np.array(label_list[i])

        if len(pos_list) <= 0 or len(pos_list) > self.max_text_nums:
            return None
        for __ in range(self.max_text_nums - len(pos_list), 0, -1):
            pos_list.append(pos_list_temp)
            pos_mask.append(pos_mask_temp)
            label_list.append(label_list_temp)

        if self.img_id == self.batch_size - 1:
            self.img_id = 0
        else:
            self.img_id += 1

        im_padded[:, :, 2] -= 0.485 * 255
        im_padded[:, :, 1] -= 0.456 * 255
        im_padded[:, :, 0] -= 0.406 * 255
        im_padded[:, :, 2] /= 255.0 * 0.229
        im_padded[:, :, 1] /= 255.0 * 0.224
        im_padded[:, :, 0] /= 255.0 * 0.225
        im_padded = im_padded.transpose((2, 0, 1))
        images = im_padded[::-1, :, :]
        tcl_maps = score_map[np.newaxis, :, :]
        tcl_label_maps = score_label_map[np.newaxis, :, :]
        border_maps = border_map.transpose((2, 0, 1))
        direction_maps = direction_map.transpose((2, 0, 1))
        training_masks = training_mask[np.newaxis, :, :]
        pos_list = np.array(pos_list)
        pos_mask = np.array(pos_mask)
        label_list = np.array(label_list)
        data["images"] = images
        data["tcl_maps"] = tcl_maps
        data["tcl_label_maps"] = tcl_label_maps
        data["border_maps"] = border_maps
        data["direction_maps"] = direction_maps
        data["training_masks"] = training_masks
        data["label_list"] = label_list
        data["pos_list"] = pos_list
        data["pos_mask"] = pos_mask
        return data