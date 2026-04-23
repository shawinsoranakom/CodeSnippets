def ocr(self,
            img,
            det=True,
            rec=True,
            mfd_res=None,
            tqdm_enable=False,
            tqdm_desc="OCR-rec Predict",
            ):
        assert isinstance(img, (np.ndarray, list, str, bytes))
        if isinstance(img, list) and det == True:
            logger.error('When input a list of images, det must be false')
            exit(0)
        img = check_img(img)
        imgs = [img]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if det and rec:
                ocr_res = []
                for img in imgs:
                    img = preprocess_image(img)
                    dt_boxes, rec_res = self.__call__(img, mfd_res=mfd_res)
                    if not dt_boxes and not rec_res:
                        ocr_res.append(None)
                        continue
                    tmp_res = [[box.tolist(), res] for box, res in zip(dt_boxes, rec_res)]
                    ocr_res.append(tmp_res)
                return ocr_res
            elif det and not rec:
                ocr_res = []
                for img in imgs:
                    img = preprocess_image(img)
                    dt_boxes, elapse = self.text_detector(img)
                    # logger.debug("dt_boxes num : {}, elapsed : {}".format(len(dt_boxes), elapse))
                    if dt_boxes is None:
                        ocr_res.append(None)
                        continue
                    if self.is_seal:
                        dt_boxes = self._seal_sort_boxes(dt_boxes)
                        img_crop_list = self._seal_crop_by_polys(img, dt_boxes)
                        self._dump_seal_debug_artifacts(img, dt_boxes, img_crop_list)
                    else:
                        dt_boxes = sorted_boxes(dt_boxes)
                        # merge_det_boxes 和 update_det_boxes 都会把poly转成bbox再转回poly，因此需要过滤所有倾斜程度较大的文本框
                        if self.enable_merge_det_boxes:
                            dt_boxes = merge_det_boxes(dt_boxes)
                        if mfd_res:
                            dt_boxes = update_det_boxes(dt_boxes, mfd_res)
                    tmp_res = [box.tolist() for box in dt_boxes]
                    ocr_res.append(tmp_res)
                return ocr_res
            elif not det and rec:
                ocr_res = []
                for img in imgs:
                    if not isinstance(img, list):
                        img = preprocess_image(img)
                        img = [img]
                    rec_res, elapse = self.text_recognizer(img, tqdm_enable=tqdm_enable, tqdm_desc=tqdm_desc)
                    # logger.debug("rec_res num  : {}, elapsed : {}".format(len(rec_res), elapse))
                    ocr_res.append(rec_res)
                return ocr_res