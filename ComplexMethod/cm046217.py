def pre_transform(self, im):
        """Preprocess images and prompts before inference.

        This method applies letterboxing to the input image and transforms the visual prompts (bounding boxes or masks)
        accordingly.

        Args:
            im (list): List of input images.

        Returns:
            (list): Preprocessed images ready for model inference.

        Raises:
            ValueError: If neither valid bounding boxes nor masks are provided in the prompts.
        """
        img = super().pre_transform(im)
        bboxes = self.prompts.pop("bboxes", None)
        masks = self.prompts.pop("masks", None)
        category = self.prompts["cls"]
        if len(img) == 1:
            visuals = self._process_single_image(img[0].shape[:2], im[0].shape[:2], category, bboxes, masks)
            prompts = visuals.unsqueeze(0).to(self.device)  # (1, N, H, W)
        else:
            # NOTE: only supports bboxes as prompts for now
            assert bboxes is not None, f"Expected bboxes, but got {bboxes}!"
            # NOTE: needs list[np.ndarray]
            assert isinstance(bboxes, list) and all(isinstance(b, np.ndarray) for b in bboxes), (
                f"Expected list[np.ndarray], but got {bboxes}!"
            )
            assert isinstance(category, list) and all(isinstance(b, np.ndarray) for b in category), (
                f"Expected list[np.ndarray], but got {category}!"
            )
            assert len(im) == len(category) == len(bboxes), (
                f"Expected same length for all inputs, but got {len(im)}vs{len(category)}vs{len(bboxes)}!"
            )
            visuals = [
                self._process_single_image(img[i].shape[:2], im[i].shape[:2], category[i], bboxes[i])
                for i in range(len(img))
            ]
            prompts = torch.nn.utils.rnn.pad_sequence(visuals, batch_first=True).to(self.device)  # (B, N, H, W)
        self.prompts = prompts.half() if self.model.fp16 else prompts.float()
        return img