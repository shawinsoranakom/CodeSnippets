def __call__(self, img, use_slice=False):
        # For image like poster with one side much greater than the other side,
        # splitting recursively and processing with overlap to enhance performance.
        MIN_BOUND_DISTANCE = 50
        dt_boxes = np.zeros((0, 4, 2), dtype=np.float32)
        elapse = 0
        if (
            img.shape[0] / img.shape[1] > 2
            and img.shape[0] > self.args.det_limit_side_len
            and use_slice
        ):
            start_h = 0
            end_h = 0
            while end_h <= img.shape[0]:
                end_h = start_h + img.shape[1] * 3 // 4
                subimg = img[start_h:end_h, :]
                if len(subimg) == 0:
                    break
                sub_dt_boxes, sub_elapse = self.predict(subimg)
                offset = start_h
                # To prevent text blocks from being cut off, roll back a certain buffer area.
                if (
                    len(sub_dt_boxes) == 0
                    or img.shape[1] - max([x[-1][1] for x in sub_dt_boxes])
                    > MIN_BOUND_DISTANCE
                ):
                    start_h = end_h
                else:
                    sorted_indices = np.argsort(sub_dt_boxes[:, 2, 1])
                    sub_dt_boxes = sub_dt_boxes[sorted_indices]
                    bottom_line = (
                        0
                        if len(sub_dt_boxes) <= 1
                        else int(np.max(sub_dt_boxes[:-1, 2, 1]))
                    )
                    if bottom_line > 0:
                        start_h += bottom_line
                        sub_dt_boxes = sub_dt_boxes[
                            sub_dt_boxes[:, 2, 1] <= bottom_line
                        ]
                    else:
                        start_h = end_h
                if len(sub_dt_boxes) > 0:
                    if dt_boxes.shape[0] == 0:
                        dt_boxes = sub_dt_boxes + np.array(
                            [0, offset], dtype=np.float32
                        )
                    else:
                        dt_boxes = np.append(
                            dt_boxes,
                            sub_dt_boxes + np.array([0, offset], dtype=np.float32),
                            axis=0,
                        )
                elapse += sub_elapse
        elif (
            img.shape[1] / img.shape[0] > 3
            and img.shape[1] > self.args.det_limit_side_len * 3
            and use_slice
        ):
            start_w = 0
            end_w = 0
            while end_w <= img.shape[1]:
                end_w = start_w + img.shape[0] * 3 // 4
                subimg = img[:, start_w:end_w]
                if len(subimg) == 0:
                    break
                sub_dt_boxes, sub_elapse = self.predict(subimg)
                offset = start_w
                if (
                    len(sub_dt_boxes) == 0
                    or img.shape[0] - max([x[-1][0] for x in sub_dt_boxes])
                    > MIN_BOUND_DISTANCE
                ):
                    start_w = end_w
                else:
                    sorted_indices = np.argsort(sub_dt_boxes[:, 2, 0])
                    sub_dt_boxes = sub_dt_boxes[sorted_indices]
                    right_line = (
                        0
                        if len(sub_dt_boxes) <= 1
                        else int(np.max(sub_dt_boxes[:-1, 1, 0]))
                    )
                    if right_line > 0:
                        start_w += right_line
                        sub_dt_boxes = sub_dt_boxes[sub_dt_boxes[:, 1, 0] <= right_line]
                    else:
                        start_w = end_w
                if len(sub_dt_boxes) > 0:
                    if dt_boxes.shape[0] == 0:
                        dt_boxes = sub_dt_boxes + np.array(
                            [offset, 0], dtype=np.float32
                        )
                    else:
                        dt_boxes = np.append(
                            dt_boxes,
                            sub_dt_boxes + np.array([offset, 0], dtype=np.float32),
                            axis=0,
                        )
                elapse += sub_elapse
        else:
            dt_boxes, elapse = self.predict(img)
        return dt_boxes, elapse