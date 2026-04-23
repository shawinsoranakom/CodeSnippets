def __call__(self, img, mfd_res=None):

        if img is None:
            logger.debug("no valid image provided")
            return None, None

        ori_im = img.copy()
        dt_boxes, elapse = self.text_detector(img)

        if dt_boxes is None:
            logger.debug("no dt_boxes found, elapsed : {}".format(elapse))
            return None, None
        else:
            pass
            # logger.debug("dt_boxes num : {}, elapsed : {}".format(len(dt_boxes), elapse))
        if self.is_seal:
            dt_boxes = self._seal_sort_boxes(dt_boxes)
            img_crop_list = self._seal_crop_by_polys(ori_im, dt_boxes)
        else:
            img_crop_list = []

            dt_boxes = sorted_boxes(dt_boxes)

            # merge_det_boxes 和 update_det_boxes 都会把poly转成bbox再转回poly，因此需要过滤所有倾斜程度较大的文本框
            if self.enable_merge_det_boxes:
                dt_boxes = merge_det_boxes(dt_boxes)

            if mfd_res:
                dt_boxes = update_det_boxes(dt_boxes, mfd_res)

            # Standard text OCR rotates tall crops before recognition.
            # Seal OCR keeps its dedicated poly-crop path above.
            for bno in range(len(dt_boxes)):
                tmp_box = copy.deepcopy(dt_boxes[bno])
                img_crop = get_rotate_crop_image_for_text_rec(ori_im, tmp_box)
                img_crop_list.append(img_crop)

        rec_res, elapse = self.text_recognizer(img_crop_list)
        # logger.debug("rec_res num  : {}, elapsed : {}".format(len(rec_res), elapse))
        if self.is_seal:
            self._dump_seal_debug_artifacts(ori_im, dt_boxes, img_crop_list, rec_res)

        filter_boxes, filter_rec_res = [], []
        for box, rec_result in zip(dt_boxes, rec_res):
            text, score = rec_result
            if score >= self.drop_score:
                filter_boxes.append(box)
                filter_rec_res.append(rec_result)

        return filter_boxes, filter_rec_res