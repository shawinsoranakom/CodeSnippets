def crop_area(
        self, im, polys, tags, hv_tags, txts, crop_background=False, max_tries=25
    ):
        """
        make random crop from the input image
        :param im:
        :param polys:  [b,4,2]
        :param tags:
        :param crop_background:
        :param max_tries: 50 -> 25
        :return:
        """
        h, w, _ = im.shape
        pad_h = h // 10
        pad_w = w // 10
        h_array = np.zeros((h + pad_h * 2), dtype=np.int32)
        w_array = np.zeros((w + pad_w * 2), dtype=np.int32)
        for poly in polys:
            poly = np.round(poly, decimals=0).astype(np.int32)
            minx = np.min(poly[:, 0])
            maxx = np.max(poly[:, 0])
            w_array[minx + pad_w : maxx + pad_w] = 1
            miny = np.min(poly[:, 1])
            maxy = np.max(poly[:, 1])
            h_array[miny + pad_h : maxy + pad_h] = 1
        # ensure the cropped area not across a text
        h_axis = np.where(h_array == 0)[0]
        w_axis = np.where(w_array == 0)[0]
        if len(h_axis) == 0 or len(w_axis) == 0:
            return im, polys, tags, hv_tags, txts
        for i in range(max_tries):
            xx = np.random.choice(w_axis, size=2)
            xmin = np.min(xx) - pad_w
            xmax = np.max(xx) - pad_w
            xmin = np.clip(xmin, 0, w - 1)
            xmax = np.clip(xmax, 0, w - 1)
            yy = np.random.choice(h_axis, size=2)
            ymin = np.min(yy) - pad_h
            ymax = np.max(yy) - pad_h
            ymin = np.clip(ymin, 0, h - 1)
            ymax = np.clip(ymax, 0, h - 1)
            if xmax - xmin < self.min_crop_size or ymax - ymin < self.min_crop_size:
                continue
            if polys.shape[0] != 0:
                poly_axis_in_area = (
                    (polys[:, :, 0] >= xmin)
                    & (polys[:, :, 0] <= xmax)
                    & (polys[:, :, 1] >= ymin)
                    & (polys[:, :, 1] <= ymax)
                )
                selected_polys = np.where(np.sum(poly_axis_in_area, axis=1) == 4)[0]
            else:
                selected_polys = []
            if len(selected_polys) == 0:
                # no text in this area
                if crop_background:
                    txts_tmp = []
                    for selected_poly in selected_polys:
                        txts_tmp.append(txts[selected_poly])
                    txts = txts_tmp
                    return (
                        im[ymin : ymax + 1, xmin : xmax + 1, :],
                        polys[selected_polys],
                        tags[selected_polys],
                        hv_tags[selected_polys],
                        txts,
                    )
                else:
                    continue
            im = im[ymin : ymax + 1, xmin : xmax + 1, :]
            polys = polys[selected_polys]
            tags = tags[selected_polys]
            hv_tags = hv_tags[selected_polys]
            txts_tmp = []
            for selected_poly in selected_polys:
                txts_tmp.append(txts[selected_poly])
            txts = txts_tmp
            polys[:, :, 0] -= xmin
            polys[:, :, 1] -= ymin
            return im, polys, tags, hv_tags, txts

        return im, polys, tags, hv_tags, txts