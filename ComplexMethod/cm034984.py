def __call__(self, ori_img, img, preds):
        scores, raw_boxes = preds["boxes"], preds["boxes_num"]
        batch_size = raw_boxes[0].shape[0]
        reg_max = int(raw_boxes[0].shape[-1] / 4 - 1)
        out_boxes_num = []
        out_boxes_list = []
        results = []
        ori_shape, input_shape, scale_factor = self.img_info(ori_img, img)

        for batch_id in range(batch_size):
            # generate centers
            decode_boxes = []
            select_scores = []
            for stride, box_distribute, score in zip(self.strides, raw_boxes, scores):
                box_distribute = box_distribute[batch_id]
                score = score[batch_id]
                # centers
                fm_h = input_shape[0] / stride
                fm_w = input_shape[1] / stride
                h_range = np.arange(fm_h)
                w_range = np.arange(fm_w)
                ww, hh = np.meshgrid(w_range, h_range)
                ct_row = (hh.flatten() + 0.5) * stride
                ct_col = (ww.flatten() + 0.5) * stride
                center = np.stack((ct_col, ct_row, ct_col, ct_row), axis=1)

                # box distribution to distance
                reg_range = np.arange(reg_max + 1)
                box_distance = box_distribute.reshape((-1, reg_max + 1))
                box_distance = softmax(box_distance, axis=1)
                box_distance = box_distance * np.expand_dims(reg_range, axis=0)
                box_distance = np.sum(box_distance, axis=1).reshape((-1, 4))
                box_distance = box_distance * stride

                # top K candidate
                topk_idx = np.argsort(score.max(axis=1))[::-1]
                topk_idx = topk_idx[: self.nms_top_k]
                center = center[topk_idx]
                score = score[topk_idx]
                box_distance = box_distance[topk_idx]

                # decode box
                decode_box = center + [-1, -1, 1, 1] * box_distance

                select_scores.append(score)
                decode_boxes.append(decode_box)

            # nms
            bboxes = np.concatenate(decode_boxes, axis=0)
            confidences = np.concatenate(select_scores, axis=0)
            picked_box_probs = []
            picked_labels = []
            for class_index in range(0, confidences.shape[1]):
                probs = confidences[:, class_index]
                mask = probs > self.score_threshold
                probs = probs[mask]
                if probs.shape[0] == 0:
                    continue
                subset_boxes = bboxes[mask, :]
                box_probs = np.concatenate([subset_boxes, probs.reshape(-1, 1)], axis=1)
                box_probs = hard_nms(
                    box_probs,
                    iou_threshold=self.nms_threshold,
                    top_k=self.keep_top_k,
                )
                picked_box_probs.append(box_probs)
                picked_labels.extend([class_index] * box_probs.shape[0])

            if len(picked_box_probs) == 0:
                out_boxes_list.append(np.empty((0, 4)))
                out_boxes_num.append(0)

            else:
                picked_box_probs = np.concatenate(picked_box_probs)

                # resize output boxes
                picked_box_probs[:, :4] = self.warp_boxes(
                    picked_box_probs[:, :4], ori_shape[batch_id]
                )
                im_scale = np.concatenate(
                    [scale_factor[batch_id][::-1], scale_factor[batch_id][::-1]]
                )
                picked_box_probs[:, :4] /= im_scale
                # clas score box
                out_boxes_list.append(
                    np.concatenate(
                        [
                            np.expand_dims(np.array(picked_labels), axis=-1),
                            np.expand_dims(picked_box_probs[:, 4], axis=-1),
                            picked_box_probs[:, :4],
                        ],
                        axis=1,
                    )
                )
                out_boxes_num.append(len(picked_labels))

        out_boxes_list = np.concatenate(out_boxes_list, axis=0)
        out_boxes_num = np.asarray(out_boxes_num).astype(np.int32)

        for dt in out_boxes_list:
            clsid, bbox, score = int(dt[0]), dt[2:], dt[1]
            label = self.labels[clsid]
            result = {"bbox": bbox, "label": label, "score": score}
            results.append(result)

        # Handle conflict where a box is simultaneously recognized as multiple labels.
        # Use IoU to find similar boxes. Prioritize labels as table, text, and others when deduplicate similar boxes.
        bboxes = np.array([x["bbox"] for x in results])
        duplicate_idx = list()
        for i in range(len(results)):
            if i in duplicate_idx:
                continue
            containments = calculate_containment(bboxes, bboxes[i, ...])
            overlaps = np.where(containments > 0.5)[0]
            if len(overlaps) > 1:
                table_box = [x for x in overlaps if results[x]["label"] == "table"]
                if len(table_box) > 0:
                    keep = sorted(
                        [(x, results[x]) for x in table_box],
                        key=lambda x: x[1]["score"],
                        reverse=True,
                    )[0][0]
                else:
                    keep = sorted(
                        [(x, results[x]) for x in overlaps],
                        key=lambda x: x[1]["score"],
                        reverse=True,
                    )[0][0]
                duplicate_idx.extend([x for x in overlaps if x != keep])
        results = [x for i, x in enumerate(results) if i not in duplicate_idx]
        return results