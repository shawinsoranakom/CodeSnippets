def postprocess(self, img, pred, **kwargs):
        row = kwargs.get("row", 50) if kwargs else 50
        col = kwargs.get("col", 30) if kwargs else 30
        h_lines_threshold = kwargs.get("h_lines_threshold", 100) if kwargs else 100
        v_lines_threshold = kwargs.get("v_lines_threshold", 15) if kwargs else 15
        angle = kwargs.get("angle", 50) if kwargs else 50
        enhance_box_line = kwargs.get("enhance_box_line", True) if kwargs else True
        morph_close = (
            kwargs.get("morph_close", enhance_box_line) if kwargs else enhance_box_line
        )  # 是否进行闭合运算以找到更多小的框
        more_h_lines = (
            kwargs.get("more_h_lines", enhance_box_line) if kwargs else enhance_box_line
        )  # 是否调整以找到更多的横线
        more_v_lines = (
            kwargs.get("more_v_lines", enhance_box_line) if kwargs else enhance_box_line
        )  # 是否调整以找到更多的横线
        extend_line = (
            kwargs.get("extend_line", enhance_box_line) if kwargs else enhance_box_line
        )  # 是否进行线段延长使得端点连接
        # 是否进行旋转修正
        rotated_fix = kwargs.get("rotated_fix") if kwargs else True
        ori_shape = img.shape
        pred = np.uint8(pred)
        hpred = copy.deepcopy(pred)  # 横线
        vpred = copy.deepcopy(pred)  # 竖线
        whereh = np.where(hpred == 1)
        wherev = np.where(vpred == 2)
        hpred[wherev] = 0
        vpred[whereh] = 0

        hpred = cv2.resize(hpred, (ori_shape[1], ori_shape[0]))
        vpred = cv2.resize(vpred, (ori_shape[1], ori_shape[0]))

        h, w = pred.shape
        hors_k = int(math.sqrt(w) * 1.2)
        vert_k = int(math.sqrt(h) * 1.2)
        hkernel = cv2.getStructuringElement(cv2.MORPH_RECT, (hors_k, 1))
        vkernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vert_k))
        vpred = cv2.morphologyEx(
            vpred, cv2.MORPH_CLOSE, vkernel, iterations=1
        )  # 先膨胀后腐蚀的过程
        if morph_close:
            hpred = cv2.morphologyEx(hpred, cv2.MORPH_CLOSE, hkernel, iterations=1)
        colboxes = get_table_line(vpred, axis=1, lineW=col)  # 竖线
        rowboxes = get_table_line(hpred, axis=0, lineW=row)  # 横线
        rboxes_row_, rboxes_col_ = [], []
        if more_h_lines:
            rboxes_row_ = adjust_lines(rowboxes, alph=h_lines_threshold, angle=angle)
        if more_v_lines:
            rboxes_col_ = adjust_lines(colboxes, alph=v_lines_threshold, angle=angle)
        rowboxes += rboxes_row_
        colboxes += rboxes_col_
        if extend_line:
            rowboxes, colboxes = final_adjust_lines(rowboxes, colboxes)
        line_img = np.zeros(img.shape[:2], dtype="uint8")
        line_img = draw_lines(line_img, rowboxes + colboxes, color=255, lineW=2)
        rotated_angle = self.cal_rotate_angle(line_img)
        if rotated_fix and abs(rotated_angle) > 0.3:
            rotated_line_img = self.rotate_image(line_img, rotated_angle)
            rotated_polygons = self.cal_region_boxes(rotated_line_img)
            polygons = self.unrotate_polygons(
                rotated_polygons, rotated_angle, line_img.shape
            )
        else:
            polygons = self.cal_region_boxes(line_img)
            rotated_polygons = polygons.copy()
        return polygons, rotated_polygons