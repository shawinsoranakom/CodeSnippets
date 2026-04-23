def _inference_features(self, features, bboxes=None, labels=None, text: list[str] | None = None):
        """Run inference on the extracted features with optional bounding boxes and labels."""
        # NOTE: priority: bboxes > text > pre-set classes
        nc = 1 if bboxes is not None else len(text) if text is not None else len(self.model.names)
        geometric_prompt = None
        if bboxes is not None:
            geometric_prompt = self._get_dummy_prompt(nc)
            for i in range(len(bboxes)):
                geometric_prompt.append_boxes(bboxes[[i]], labels[[i]])
            if text is None:
                text = ["visual"]  # bboxes needs this `visual` text prompt if no text passed
        if text is not None and self.model.names != text:
            self.model.set_classes(text=text)
        outputs = self.model.forward_grounding(
            backbone_out=features,
            text_ids=torch.arange(nc, device=self.device, dtype=torch.long),
            geometric_prompt=geometric_prompt,
        )
        return outputs