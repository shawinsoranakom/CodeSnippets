def execute(cls, bboxes, image=None) -> io.NodeOutput:
        # Normalise to list[list[dict]], then fit to batch size B.
        B = image.shape[0] if image is not None else 1
        if isinstance(bboxes, dict):
            bboxes = [[bboxes]]
        elif not isinstance(bboxes, list) or not bboxes:
            bboxes = [[]]
        elif isinstance(bboxes[0], dict):
            bboxes = [bboxes]  # flat list → same detections for every image

        if len(bboxes) == 1:
            bboxes = bboxes * B
        bboxes = (bboxes + [[]] * B)[:B]

        if image is None:
            B = len(bboxes)
            max_w = max((int(d["x"] + d["width"])  for frame in bboxes for d in frame), default=640)
            max_h = max((int(d["y"] + d["height"]) for frame in bboxes for d in frame), default=640)
            image = torch.zeros((B, max_h, max_w, 3), dtype=torch.float32)

        all_out_images = []
        for i in range(B):
            detections = bboxes[i]
            if detections:
                boxes  = torch.tensor([[d["x"], d["y"], d["x"] + d["width"], d["y"] + d["height"]] for d in detections])
                labels = [d.get("label") if d.get("label") in COCO_CLASSES else None for d in detections]
                scores = torch.tensor([d.get("score", 1.0) for d in detections])
            else:
                boxes  = torch.zeros((0, 4))
                labels = []
                scores = torch.zeros((0,))

            pil_image = image[i].movedim(-1, 0)
            img = ToPILImage()(pil_image)
            if detections:
                img = cls.draw_detections(img, boxes, labels, scores)
            all_out_images.append(ToTensor()(img).unsqueeze(0).movedim(1, -1))

        out_images = torch.cat(all_out_images, dim=0).to(comfy.model_management.intermediate_device())
        return io.NodeOutput(out_images)