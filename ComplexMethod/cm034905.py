def forward(self, preds, labels):
        """Compute Drrg loss."""

        assert isinstance(preds, tuple)
        (
            gt_text_mask,
            gt_center_region_mask,
            gt_mask,
            gt_top_height_map,
            gt_bot_height_map,
            gt_sin_map,
            gt_cos_map,
        ) = labels[1:8]

        downsample_ratio = self.downsample_ratio

        pred_maps, gcn_data = preds
        pred_text_region = pred_maps[:, 0, :, :]
        pred_center_region = pred_maps[:, 1, :, :]
        pred_sin_map = pred_maps[:, 2, :, :]
        pred_cos_map = pred_maps[:, 3, :, :]
        pred_top_height_map = pred_maps[:, 4, :, :]
        pred_bot_height_map = pred_maps[:, 5, :, :]
        feature_sz = pred_maps.shape

        # bitmask 2 tensor
        mapping = {
            "gt_text_mask": paddle.cast(gt_text_mask, "float32"),
            "gt_center_region_mask": paddle.cast(gt_center_region_mask, "float32"),
            "gt_mask": paddle.cast(gt_mask, "float32"),
            "gt_top_height_map": paddle.cast(gt_top_height_map, "float32"),
            "gt_bot_height_map": paddle.cast(gt_bot_height_map, "float32"),
            "gt_sin_map": paddle.cast(gt_sin_map, "float32"),
            "gt_cos_map": paddle.cast(gt_cos_map, "float32"),
        }
        gt = {}
        for key, value in mapping.items():
            gt[key] = value
            if abs(downsample_ratio - 1.0) < 1e-2:
                gt[key] = self.bitmasks2tensor(gt[key], feature_sz[2:])
            else:
                gt[key] = [item.rescale(downsample_ratio) for item in gt[key]]
                gt[key] = self.bitmasks2tensor(gt[key], feature_sz[2:])
                if key in ["gt_top_height_map", "gt_bot_height_map"]:
                    gt[key] = [item * downsample_ratio for item in gt[key]]
            gt[key] = [item for item in gt[key]]

        scale = paddle.sqrt(1.0 / (pred_sin_map**2 + pred_cos_map**2 + 1e-8))
        pred_sin_map = pred_sin_map * scale
        pred_cos_map = pred_cos_map * scale

        loss_text = self.balance_bce_loss(
            F.sigmoid(pred_text_region), gt["gt_text_mask"][0], gt["gt_mask"][0]
        )

        text_mask = gt["gt_text_mask"][0] * gt["gt_mask"][0]
        negative_text_mask = (1 - gt["gt_text_mask"][0]) * gt["gt_mask"][0]
        loss_center_map = F.binary_cross_entropy(
            F.sigmoid(pred_center_region),
            gt["gt_center_region_mask"][0],
            reduction="none",
        )
        if int(text_mask.sum()) > 0:
            loss_center_positive = paddle.sum(loss_center_map * text_mask) / paddle.sum(
                text_mask
            )
        else:
            loss_center_positive = paddle.to_tensor(0.0)
        loss_center_negative = paddle.sum(
            loss_center_map * negative_text_mask
        ) / paddle.sum(negative_text_mask)
        loss_center = loss_center_positive + 0.5 * loss_center_negative

        center_mask = gt["gt_center_region_mask"][0] * gt["gt_mask"][0]
        if int(center_mask.sum()) > 0:
            map_sz = pred_top_height_map.shape
            ones = paddle.ones(map_sz, dtype="float32")
            loss_top = F.smooth_l1_loss(
                pred_top_height_map / (gt["gt_top_height_map"][0] + 1e-2),
                ones,
                reduction="none",
            )
            loss_bot = F.smooth_l1_loss(
                pred_bot_height_map / (gt["gt_bot_height_map"][0] + 1e-2),
                ones,
                reduction="none",
            )
            gt_height = gt["gt_top_height_map"][0] + gt["gt_bot_height_map"][0]
            loss_height = paddle.sum(
                (paddle.log(gt_height + 1) * (loss_top + loss_bot)) * center_mask
            ) / paddle.sum(center_mask)

            loss_sin = paddle.sum(
                F.smooth_l1_loss(pred_sin_map, gt["gt_sin_map"][0], reduction="none")
                * center_mask
            ) / paddle.sum(center_mask)
            loss_cos = paddle.sum(
                F.smooth_l1_loss(pred_cos_map, gt["gt_cos_map"][0], reduction="none")
                * center_mask
            ) / paddle.sum(center_mask)
        else:
            loss_height = paddle.to_tensor(0.0)
            loss_sin = paddle.to_tensor(0.0)
            loss_cos = paddle.to_tensor(0.0)

        loss_gcn = self.gcn_loss(gcn_data)

        loss = loss_text + loss_center + loss_height + loss_sin + loss_cos + loss_gcn
        results = dict(
            loss=loss,
            loss_text=loss_text,
            loss_center=loss_center,
            loss_height=loss_height,
            loss_sin=loss_sin,
            loss_cos=loss_cos,
            loss_gcn=loss_gcn,
        )

        return results