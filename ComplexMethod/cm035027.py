def __call__(self, data):
        im = data["image"]
        text_polys = data["polys"]
        text_tags = data["ignore_tags"]
        if im is None:
            return None
        if text_polys.shape[0] == 0:
            return None

        h, w, _ = im.shape
        text_polys, text_tags, hv_tags = self.check_and_validate_polys(
            text_polys, text_tags, (h, w)
        )

        if text_polys.shape[0] == 0:
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

        h, w, _ = im.shape
        if max(h, w) > 2048:
            rd_scale = 2048.0 / max(h, w)
            im = cv2.resize(im, dsize=None, fx=rd_scale, fy=rd_scale)
            text_polys *= rd_scale
        h, w, _ = im.shape
        if min(h, w) < 16:
            return None

        # no background
        im, text_polys, text_tags, hv_tags = self.crop_area(
            im, text_polys, text_tags, hv_tags, crop_background=False
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
        std_ratio = float(self.input_size) / max(new_w, new_h)
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
        if min(new_w, new_h) < self.input_size * 0.5:
            return None

        im_padded = np.ones((self.input_size, self.input_size, 3), dtype=np.float32)
        im_padded[:, :, 2] = 0.485 * 255
        im_padded[:, :, 1] = 0.456 * 255
        im_padded[:, :, 0] = 0.406 * 255

        # Random the start position
        del_h = self.input_size - new_h
        del_w = self.input_size - new_w
        sh, sw = 0, 0
        if del_h > 1:
            sh = int(np.random.rand() * del_h)
        if del_w > 1:
            sw = int(np.random.rand() * del_w)

        # Padding
        im_padded[sh : sh + new_h, sw : sw + new_w, :] = im.copy()
        text_polys[:, :, 0] += sw
        text_polys[:, :, 1] += sh

        score_map, border_map, training_mask = self.generate_tcl_label(
            (self.input_size, self.input_size), text_polys, text_tags, 0.25
        )

        # SAST head
        tvo_map, tco_map = self.generate_tvo_and_tco(
            (self.input_size, self.input_size),
            text_polys,
            text_tags,
            tcl_ratio=0.3,
            ds_ratio=0.25,
        )
        # print("test--------tvo_map shape:", tvo_map.shape)

        im_padded[:, :, 2] -= 0.485 * 255
        im_padded[:, :, 1] -= 0.456 * 255
        im_padded[:, :, 0] -= 0.406 * 255
        im_padded[:, :, 2] /= 255.0 * 0.229
        im_padded[:, :, 1] /= 255.0 * 0.224
        im_padded[:, :, 0] /= 255.0 * 0.225
        im_padded = im_padded.transpose((2, 0, 1))

        data["image"] = im_padded[::-1, :, :]
        data["score_map"] = score_map[np.newaxis, :, :]
        data["border_map"] = border_map.transpose((2, 0, 1))
        data["training_mask"] = training_mask[np.newaxis, :, :]
        data["tvo_map"] = tvo_map.transpose((2, 0, 1))
        data["tco_map"] = tco_map.transpose((2, 0, 1))
        return data