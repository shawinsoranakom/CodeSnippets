def postprocess(self, boxes, inputs, thr=0.25):
        arr = np.squeeze(boxes)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        results = []
        if arr.shape[1] == 6:
            # [x1,y1,x2,y2,score,cls]
            m = arr[:, 4] >= thr
            arr = arr[m]
            if arr.size == 0:
                return []
            xyxy = arr[:, :4].astype(np.float32)
            scores = arr[:, 4].astype(np.float32)
            cls_ids = arr[:, 5].astype(np.int32)

            if "pad" in inputs:
                dw, dh = inputs["pad"]
                sx, sy = inputs["scale_factor"]
                xyxy[:, [0, 2]] -= dw
                xyxy[:, [1, 3]] -= dh
                xyxy *= np.array([sx, sy, sx, sy], dtype=np.float32)
            else:
                # backup
                sx, sy = inputs["scale_factor"]
                xyxy *= np.array([sx, sy, sx, sy], dtype=np.float32)

            keep_indices = []
            for c in np.unique(cls_ids):
                idx = np.where(cls_ids == c)[0]
                k = nms(xyxy[idx], scores[idx], 0.45)
                keep_indices.extend(idx[k])

            for i in keep_indices:
                cid = int(cls_ids[i])
                if 0 <= cid < len(self.labels):
                    results.append({"type": self.labels[cid].lower(), "bbox": [float(t) for t in xyxy[i].tolist()], "score": float(scores[i])})
            return results

        raise ValueError(f"Unexpected output shape: {arr.shape}")