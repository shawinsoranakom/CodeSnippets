def get_panoptic_annotations(self, label, num_class_obj):
        annotation_classes = label["classes"]
        annotation_masks = label["masks"]

        texts = ["an panoptic photo"] * self.num_text
        classes = []
        masks = []
        for idx in range(len(annotation_classes)):
            class_id = annotation_classes[idx]
            mask = annotation_masks[idx] if hasattr(annotation_masks[idx], "data") else annotation_masks[idx]
            if not np.all(mask == 0):
                cls_name = self.metadata[str(class_id)]
                classes.append(class_id)
                masks.append(mask)
                num_class_obj[cls_name] += 1

        num = 0
        for i, cls_name in enumerate(self.metadata["class_names"]):
            if num_class_obj[cls_name] > 0:
                for _ in range(num_class_obj[cls_name]):
                    if num >= len(texts):
                        break
                    texts[num] = f"a photo with a {cls_name}"
                    num += 1

        classes = np.array(classes) if classes else np.array([], dtype=np.int64)
        # Stack masks into a 3D array (num_masks, H, W) to match torchvision version
        if masks:
            masks = np.stack(masks, axis=0)
        else:
            # Empty masks - use shape from first annotation mask if available
            if annotation_masks and len(annotation_masks) > 0:
                mask_shape = annotation_masks[0].shape[-2:] if hasattr(annotation_masks[0], "shape") else (0, 0)
            else:
                mask_shape = (0, 0)
            masks = np.zeros((0, *mask_shape), dtype=np.float32)
        return classes, masks, texts