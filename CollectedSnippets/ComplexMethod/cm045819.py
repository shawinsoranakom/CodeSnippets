def batch_predict(
        self, imgs: List[Dict], det_batch_size: int, batch_size: int = 16
    ) -> None:
        """
        批量预测传入的包含图片信息列表的旋转信息，并且将旋转过的图片正确地旋转回来
        """
        RESOLUTION_GROUP_STRIDE = 128
        # 跳过长宽比小于1.2的图片
        resolution_groups = defaultdict(list)
        for img in imgs:
            # RGB图像转换BGR
            bgr_img: np.ndarray = cv2.cvtColor(np.asarray(img["table_img"]), cv2.COLOR_RGB2BGR)
            img["table_img_bgr"] = bgr_img
            img_height, img_width = bgr_img.shape[:2]
            img_aspect_ratio = img_height / img_width if img_width > 0 else 1.0
            if img_aspect_ratio > 1.2:
                # 归一化尺寸到RESOLUTION_GROUP_STRIDE的倍数
                normalized_h = ((img_height + RESOLUTION_GROUP_STRIDE) // RESOLUTION_GROUP_STRIDE) * RESOLUTION_GROUP_STRIDE  # 向上取整到RESOLUTION_GROUP_STRIDE的倍数
                normalized_w = ((img_width + RESOLUTION_GROUP_STRIDE) // RESOLUTION_GROUP_STRIDE) * RESOLUTION_GROUP_STRIDE
                group_key = (normalized_h, normalized_w)
                resolution_groups[group_key].append(img)

        # 对每个分辨率组进行批处理
        rotated_imgs = []
        for group_key, group_imgs in tqdm(resolution_groups.items(), desc="Table-ori cls stage1 predict", disable=True):
            # 计算目标尺寸（组内最大尺寸，向上取整到RESOLUTION_GROUP_STRIDE的倍数）
            max_h = max(img["table_img_bgr"].shape[0] for img in group_imgs)
            max_w = max(img["table_img_bgr"].shape[1] for img in group_imgs)
            target_h = ((max_h + RESOLUTION_GROUP_STRIDE - 1) // RESOLUTION_GROUP_STRIDE) * RESOLUTION_GROUP_STRIDE
            target_w = ((max_w + RESOLUTION_GROUP_STRIDE - 1) // RESOLUTION_GROUP_STRIDE) * RESOLUTION_GROUP_STRIDE

            # 对所有图像进行padding到统一尺寸
            batch_images = []
            for img in group_imgs:
                bgr_img = img["table_img_bgr"]
                h, w = bgr_img.shape[:2]
                # 创建目标尺寸的白色背景
                padded_img = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
                # 将原图像粘贴到左上角
                padded_img[:h, :w] = bgr_img
                batch_images.append(padded_img)

            # 批处理检测
            batch_results = self.ocr_engine.text_detector.batch_predict(
                batch_images, min(len(batch_images), det_batch_size)
            )

            # 根据批处理结果检测图像是否旋转,旋转的图像放入列表中，继续进行旋转角度的预测

            for index, (img_info, (dt_boxes, elapse)) in enumerate(
                zip(group_imgs, batch_results)
            ):
                vertical_count = 0
                for box_ocr_res in dt_boxes:
                    p1, p2, p3, p4 = box_ocr_res

                    # Calculate width and height
                    width = p3[0] - p1[0]
                    height = p3[1] - p1[1]

                    aspect_ratio = width / height if height > 0 else 1.0

                    # Count vertical text boxes
                    if aspect_ratio < 0.8:  # Taller than wide - vertical text
                        vertical_count += 1

                if vertical_count >= len(dt_boxes) * 0.28 and vertical_count >= 3:
                    rotated_imgs.append(img_info)

        # 对旋转的图片进行旋转角度预测
        if len(rotated_imgs) > 0:
            imgs = self.list_2_batch(rotated_imgs, batch_size=batch_size)
            with tqdm(total=len(rotated_imgs), desc="Table-ori cls stage2 predict", disable=True) as pbar:
                for img_batch in imgs:
                    x = self.batch_preprocess(img_batch)
                    results = self.sess.run(None, {"x": x})
                    for img_info, res in zip(rotated_imgs, results[0]):
                        label = self.labels[np.argmax(res)]
                        self.img_rotate(img_info, label)
                        pbar.update(1)