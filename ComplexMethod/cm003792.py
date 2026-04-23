def get_instance_annotations(self, label, num_class_obj):
        annotation_classes = label["classes"]
        annotation_masks = label["masks"]

        texts = ["an instance photo"] * self.num_text
        classes = []
        masks = []

        for idx in range(len(annotation_classes)):
            class_id = annotation_classes[idx]
            mask = annotation_masks[idx]

            if class_id in self.metadata["thing_ids"]:
                if not torch.all(mask == 0):
                    cls_name = self.metadata[str(class_id.cpu().item())]
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

        classes = torch.stack(classes)
        masks = torch.stack(masks)
        return classes, masks, texts