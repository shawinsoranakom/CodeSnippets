def add_prompt(
        self,
        frame_idx,
        text=None,
        bboxes=None,
        labels=None,
        inference_state=None,
    ):
        """Add text, point or box prompts on a single frame. This method returns the inference outputs only on the
        prompted frame.

        Note that text prompts are NOT associated with a particular frame (i.e. they apply
        to all frames). However, we only run inference on the frame specified in `frame_idx`.
        """
        inference_state = inference_state or self.inference_state
        assert text is not None or bboxes is not None, "at least one type of prompt (text, boxes) must be provided"

        # 1) handle text prompt
        use_text = text is not None
        text = text if use_text else "visual"
        text_batch = [text] if isinstance(text, str) else text
        inference_state["text_prompt"] = text if use_text else None
        n = len(text_batch)
        text_ids = torch.arange(n, device=self.device, dtype=torch.long)
        inference_state["text_ids"] = text_ids
        if text is not None and self.model.names != text:
            self.model.set_classes(text=text)

        # 2) handle box prompt
        bboxes, labels = self._prepare_geometric_prompts(self.batch[1][0].shape[:2], bboxes, labels)
        assert (bboxes is not None) == (labels is not None)
        geometric_prompt = self._get_dummy_prompt(num_prompts=n)
        if bboxes is not None:
            for i in range(len(bboxes)):
                geometric_prompt.append_boxes(bboxes[[i]], labels[[i]])
        inference_state["per_frame_geometric_prompt"][frame_idx] = geometric_prompt
        out = self._run_single_frame_inference(frame_idx, reverse=False, inference_state=inference_state)
        return frame_idx, out