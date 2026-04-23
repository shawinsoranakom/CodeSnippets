def __call__(self, data):
        img = data["image"]
        bboxes = data["polys"]
        words = data["texts"]
        scale_factor = data["scale_factor"]

        gt_instance = np.zeros(img.shape[0:2], dtype="uint8")  # h,w
        training_mask = np.ones(img.shape[0:2], dtype="uint8")
        training_mask_distance = np.ones(img.shape[0:2], dtype="uint8")

        for i in range(len(bboxes)):
            bboxes[i] = np.reshape(
                bboxes[i]
                * ([scale_factor[0], scale_factor[1]] * (bboxes[i].shape[0] // 2)),
                (bboxes[i].shape[0] // 2, 2),
            ).astype("int32")

        for i in range(len(bboxes)):
            # different value for different bbox
            cv2.drawContours(gt_instance, [bboxes[i]], -1, i + 1, -1)

            # set training mask to 0
            cv2.drawContours(training_mask, [bboxes[i]], -1, 0, -1)

            # for not accurate annotation, use training_mask_distance
            if words[i] == "###" or words[i] == "???":
                cv2.drawContours(training_mask_distance, [bboxes[i]], -1, 0, -1)

        # make shrink
        gt_kernel_instance = np.zeros(img.shape[0:2], dtype="uint8")
        kernel_bboxes = self.shrink(bboxes, self.kernel_scale)
        for i in range(len(bboxes)):
            cv2.drawContours(gt_kernel_instance, [kernel_bboxes[i]], -1, i + 1, -1)

            # for training mask, kernel and background= 1, box region=0
            if words[i] != "###" and words[i] != "???":
                cv2.drawContours(training_mask, [kernel_bboxes[i]], -1, 1, -1)

        gt_kernel = gt_kernel_instance.copy()
        # for gt_kernel, kernel = 1
        gt_kernel[gt_kernel > 0] = 1

        # shrink 2 times
        tmp1 = gt_kernel_instance.copy()
        erode_kernel = np.ones((3, 3), np.uint8)
        tmp1 = cv2.erode(tmp1, erode_kernel, iterations=1)
        tmp2 = tmp1.copy()
        tmp2 = cv2.erode(tmp2, erode_kernel, iterations=1)

        # compute text region
        gt_kernel_inner = tmp1 - tmp2

        # gt_instance: text instance, bg=0, diff word use diff value
        # training_mask: text instance mask, word=0，kernel and bg=1
        # gt_kernel_instance: text kernel instance, bg=0, diff word use diff value
        # gt_kernel: text_kernel, bg=0，diff word use same value
        # gt_kernel_inner: text kernel reference
        # training_mask_distance: word without anno = 0, else 1

        data["image"] = [
            img,
            gt_instance,
            training_mask,
            gt_kernel_instance,
            gt_kernel,
            gt_kernel_inner,
            training_mask_distance,
        ]
        return data