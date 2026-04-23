def execute(cls, keypoints, scale, force_square) -> io.NodeOutput:
        all_bboxes = []
        for frame in keypoints:
            h = frame["canvas_height"]
            w = frame["canvas_width"]
            frame_bboxes = []
            for person in frame["people"]:
                face_flat = person.get("face_keypoints_2d", [])
                if not face_flat:
                    continue
                # Parse absolute-pixel face keypoints (70 kp: 68 landmarks + REye + LEye)
                face_arr = np.array(face_flat, dtype=np.float32).reshape(-1, 3)
                face_xy  = face_arr[:, :2]  # (70, 2) in absolute pixels

                kp_norm = face_xy / np.array([w, h], dtype=np.float32)
                kp_padded = np.vstack([np.zeros((1, 2), dtype=np.float32), kp_norm])  # (71, 2)

                x1, x2, y1, y2 = get_face_bboxes(kp_padded, scale, (h, w))
                if x2 > x1 and y2 > y1:
                    if force_square:
                        bw, bh = x2 - x1, y2 - y1
                        if bw != bh:
                            side = max(bw, bh)
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            half = side // 2
                            x1 = max(0, cx - half)
                            y1 = max(0, cy - half)
                            x2 = min(w, x1 + side)
                            y2 = min(h, y1 + side)
                            # Re-anchor if clamped
                            x1 = max(0, x2 - side)
                            y1 = max(0, y2 - side)
                    frame_bboxes.append({"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1})

            all_bboxes.append(frame_bboxes)

        return io.NodeOutput(all_bboxes)