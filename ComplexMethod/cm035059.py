def projection_cx(self, box_img):
        box_gray_img = cv2.cvtColor(box_img, cv2.COLOR_BGR2GRAY)
        h, w = box_gray_img.shape
        # 灰度图片进行二值化处理
        ret, thresh1 = cv2.threshold(box_gray_img, 200, 255, cv2.THRESH_BINARY_INV)
        # 纵向腐蚀
        if h < w:
            kernel = np.ones((2, 1), np.uint8)
            erode = cv2.erode(thresh1, kernel, iterations=1)
        else:
            erode = thresh1
        # 水平膨胀
        kernel = np.ones((1, 5), np.uint8)
        erosion = cv2.dilate(erode, kernel, iterations=1)
        # 水平投影
        projection_map = np.ones_like(erosion)
        project_val_array = [0 for _ in range(0, h)]

        for j in range(0, h):
            for i in range(0, w):
                if erosion[j, i] == 255:
                    project_val_array[j] += 1
        # 根据数组，获取切割点
        start_idx = 0  # 记录进入字符区的索引
        end_idx = 0  # 记录进入空白区域的索引
        in_text = False  # 是否遍历到了字符区内
        box_list = []
        spilt_threshold = 0
        for i in range(len(project_val_array)):
            if (
                in_text == False and project_val_array[i] > spilt_threshold
            ):  # 进入字符区了
                in_text = True
                start_idx = i
            elif (
                project_val_array[i] <= spilt_threshold and in_text == True
            ):  # 进入空白区了
                end_idx = i
                in_text = False
                if end_idx - start_idx <= 2:
                    continue
                box_list.append((start_idx, end_idx + 1))

        if in_text:
            box_list.append((start_idx, h - 1))
        # 绘制投影直方图
        for j in range(0, h):
            for i in range(0, project_val_array[j]):
                projection_map[j, i] = 0
        split_bbox_list = []
        if len(box_list) > 1:
            for i, (h_start, h_end) in enumerate(box_list):
                if i == 0:
                    h_start = 0
                if i == len(box_list):
                    h_end = h
                word_img = erosion[h_start : h_end + 1, :]
                word_h, word_w = word_img.shape
                w_split_list, w_projection_map = self.projection(
                    word_img.T, word_w, word_h
                )
                w_start, w_end = w_split_list[0][0], w_split_list[-1][1]
                if h_start > 0:
                    h_start -= 1
                h_end += 1
                word_img = box_img[h_start : h_end + 1 :, w_start : w_end + 1, :]
                split_bbox_list.append([w_start, h_start, w_end, h_end])
        else:
            split_bbox_list.append([0, 0, w, h])
        return split_bbox_list