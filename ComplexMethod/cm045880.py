def batch_predict(
        self,
        images_mfd_res: list,
        images: list,
        batch_size: int = 64,
        interline_enable: bool = True,
    ) -> list:
        if not images_mfd_res:
            return []

        if len(images_mfd_res) != len(images):
            raise ValueError("images_mfd_res and images must have the same length.")

        images_formula_list = []
        mf_image_list = []
        backfill_list = []
        image_info = []

        for mfd_res, image in zip(images_mfd_res, images):
            formula_list, crop_targets = self._build_formula_items(
                mfd_res,
                image,
                interline_enable=interline_enable,
            )

            for formula_item, (xmin, ymin, xmax, ymax) in crop_targets:
                bbox_img = image[ymin:ymax, xmin:xmax]
                area = (xmax - xmin) * (ymax - ymin)

                curr_idx = len(mf_image_list)
                image_info.append((area, curr_idx, bbox_img))
                mf_image_list.append(bbox_img)
                backfill_list.append(formula_item)

            images_formula_list.append(formula_list)

        if not image_info:
            return images_formula_list

        image_info.sort(key=lambda x: x[0])
        sorted_areas = [x[0] for x in image_info]
        sorted_indices = [x[1] for x in image_info]
        sorted_images = [x[2] for x in image_info]
        index_mapping = {
            new_idx: old_idx for new_idx, old_idx in enumerate(sorted_indices)
        }

        formula_requested_batch_size = max(1, batch_size // 2)
        batch_groups = build_mfr_batch_groups(
            sorted_areas,
            formula_requested_batch_size,
        )

        batch_imgs = self.pre_tfs["UniMERNetImgDecode"](imgs=sorted_images)
        batch_imgs = self.pre_tfs["UniMERNetTestTransform"](imgs=batch_imgs)
        batch_imgs = self.pre_tfs["LatexImageFormat"](imgs=batch_imgs)
        inp = self.pre_tfs["ToBatch"](imgs=batch_imgs)
        inp = torch.from_numpy(inp[0]).to(self.device)

        rec_formula = []
        with torch.no_grad():
            with tqdm(total=len(inp), desc="MFR Predict") as pbar:
                for batch_group in batch_groups:
                    batch_data = inp[batch_group]
                    batch_preds = [self.net(batch_data)]
                    batch_preds = [p.reshape([-1]) for p in batch_preds[0]]
                    batch_preds = [bp.cpu().numpy() for bp in batch_preds]
                    rec_formula += self.post_op(batch_preds)
                    pbar.update(len(batch_group))

        unsorted_results = [""] * len(rec_formula)
        for new_idx, latex in enumerate(rec_formula):
            original_idx = index_mapping[new_idx]
            unsorted_results[original_idx] = latex

        for res, latex in zip(backfill_list, unsorted_results):
            res["latex"] = latex

        return images_formula_list