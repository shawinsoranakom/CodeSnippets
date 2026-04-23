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

        batch_groups = build_mfr_batch_groups(sorted_areas, batch_size)
        dataset = MathDataset(sorted_images, transform=self.model.transform)
        dataloader = DataLoader(dataset, batch_sampler=batch_groups, num_workers=0)

        mfr_res = []
        with tqdm(total=len(sorted_images), desc="MFR Predict") as pbar:
            for batch_group, mf_img in zip(batch_groups, dataloader):
                current_batch_size = len(batch_group)
                mf_img = mf_img.to(dtype=self.model.dtype)
                mf_img = mf_img.to(self.device)
                with torch.no_grad():
                    output = self.model.generate(
                        {"image": mf_img},
                        batch_size=current_batch_size,
                    )
                mfr_res.extend(output["fixed_str"])
                pbar.update(current_batch_size)

        unsorted_results = [""] * len(mfr_res)
        for new_idx, latex in enumerate(mfr_res):
            original_idx = index_mapping[new_idx]
            unsorted_results[original_idx] = latex

        for res, latex in zip(backfill_list, unsorted_results):
            res["latex"] = latex

        return images_formula_list