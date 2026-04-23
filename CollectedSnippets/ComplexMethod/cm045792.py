def _dump_seal_debug_artifacts(self, input_image, dt_boxes, img_crop_list, rec_res=None):
        if not self._seal_debug_dir:
            return

        sample_dir = os.path.join(
            self._seal_debug_dir,
            f"sample_{self._seal_debug_counter:04d}",
        )
        self._seal_debug_counter += 1
        os.makedirs(sample_dir, exist_ok=True)

        cv2.imwrite(os.path.join(sample_dir, "input.png"), input_image)

        det_vis = input_image.copy()
        for index, box in enumerate(dt_boxes or []):
            points = np.asarray(box, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(det_vis, [points], isClosed=True, color=(0, 0, 255), thickness=2)
            anchor = tuple(np.asarray(box[0], dtype=np.int32).tolist())
            cv2.putText(
                det_vis,
                str(index),
                anchor,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2,
                cv2.LINE_AA,
            )
        cv2.imwrite(os.path.join(sample_dir, "det_vis.png"), det_vis)

        records = []
        for index, crop_img in enumerate(img_crop_list or []):
            crop_name = f"crop_{index:02d}.png"
            cv2.imwrite(os.path.join(sample_dir, crop_name), crop_img)
            record = {
                "index": index,
                "crop_path": crop_name,
            }
            if rec_res is not None and index < len(rec_res):
                text, score = rec_res[index]
                record["text"] = text
                record["score"] = float(score)
            records.append(record)

        with open(os.path.join(sample_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)