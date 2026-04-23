def summary(self, normalize: bool = False, decimals: int = 5) -> list[dict[str, Any]]:
        """Convert inference results to a summarized dictionary with optional normalization for box coordinates.

        This method creates a list of detection dictionaries, each containing information about a single detection or
        classification result. For classification tasks, it returns the top 5 classes and their
        confidences. For detection tasks, it includes class information, bounding box coordinates, and
        optionally mask segments and keypoints.

        Args:
            normalize (bool): Whether to normalize bounding box coordinates by image dimensions.
            decimals (int): Number of decimal places to round the output values to.

        Returns:
            (list[dict[str, Any]]): A list of dictionaries, each containing summarized information for a single
                detection or classification result. The structure of each dictionary varies based on the task type
                (classification or detection) and available information (boxes, masks, keypoints).

        Examples:
            >>> results = model("image.jpg")
            >>> for result in results:
            ...     summary = result.summary()
            ...     print(summary)
        """
        # Create list of detection dictionaries
        results = []
        if self.probs is not None:
            # Return top 5 classification results
            for class_id, conf in zip(self.probs.top5, self.probs.top5conf.tolist()):
                class_id = int(class_id)
                results.append(
                    {
                        "name": self.names[class_id],
                        "class": class_id,
                        "confidence": round(conf, decimals),
                    }
                )
            return results

        is_obb = self.obb is not None
        data = self.obb if is_obb else self.boxes
        h, w = self.orig_shape if normalize else (1, 1)
        for i, row in enumerate(data):  # xyxy, track_id if tracking, conf, class_id
            class_id, conf = int(row.cls), round(row.conf.item(), decimals)
            box = (row.xyxyxyxy if is_obb else row.xyxy).squeeze().reshape(-1, 2).tolist()
            xy = {}
            for j, b in enumerate(box):
                xy[f"x{j + 1}"] = round(b[0] / w, decimals)
                xy[f"y{j + 1}"] = round(b[1] / h, decimals)
            result = {"name": self.names[class_id], "class": class_id, "confidence": conf, "box": xy}
            if data.is_track:
                result["track_id"] = int(row.id.item())  # track ID
            if self.masks:
                result["segments"] = {
                    "x": (self.masks.xy[i][:, 0] / w).round(decimals).tolist(),
                    "y": (self.masks.xy[i][:, 1] / h).round(decimals).tolist(),
                }
            if self.keypoints is not None:
                kpt = self.keypoints[i]
                if kpt.has_visible:
                    x, y, visible = kpt.data[0].cpu().unbind(dim=1)
                else:
                    x, y = kpt.data[0].cpu().unbind(dim=1)
                result["keypoints"] = {
                    "x": (x / w).numpy().round(decimals).tolist(),
                    "y": (y / h).numpy().round(decimals).tolist(),
                }
                if kpt.has_visible:
                    result["keypoints"]["visible"] = visible.numpy().round(decimals).tolist()
            results.append(result)

        return results