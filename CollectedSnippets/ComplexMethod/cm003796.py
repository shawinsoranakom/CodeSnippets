def __call__(self, images=None, task_inputs=None, segmentation_maps=None, **kwargs):
        r"""
        task_inputs (`str` or `list[str]`, *required*):
            The task type(s) for segmentation. Must be one or more of `"semantic"`, `"instance"`, or `"panoptic"`.
            Can be a single string for a single image, or a list of strings (one per image) for batch processing.
            The task type determines which type of segmentation the model will perform on the input images.
        segmentation_maps (`ImageInput`, *optional*):
            The corresponding semantic segmentation maps with the pixel-wise annotations.

            (`bool`, *optional*, defaults to `True`):
            Whether or not to pad images up to the largest image in a batch and create a pixel mask.

            If left to the default, will return a pixel mask that is:

            - 1 for pixels that are real (i.e. **not masked**),
            - 0 for pixels that are padding (i.e. **masked**).

        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:
            - **task_inputs** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
        """

        if task_inputs is None:
            raise ValueError("You have to specify the task_input. Found None.")
        elif images is None:
            raise ValueError("You have to specify the image. Found None.")

        if not all(task in ["semantic", "instance", "panoptic"] for task in task_inputs):
            raise ValueError("task_inputs must be semantic, instance, or panoptic.")

        encoded_inputs = self.image_processor(images, task_inputs, segmentation_maps, **kwargs)

        if isinstance(task_inputs, str):
            task_inputs = [task_inputs]

        if isinstance(task_inputs, list) and all(isinstance(task_input, str) for task_input in task_inputs):
            task_token_inputs = []
            for task in task_inputs:
                task_input = f"the task is {task}"
                task_token_inputs.append(task_input)
            encoded_inputs["task_inputs"] = self._preprocess_text(task_token_inputs, max_length=self.task_seq_length)
        else:
            raise TypeError("Task Inputs should be a string or a list of strings.")

        if hasattr(encoded_inputs, "text_inputs"):
            texts_list = encoded_inputs.text_inputs

            text_inputs = []
            for texts in texts_list:
                text_input_list = self._preprocess_text(texts, max_length=self.max_seq_length)
                text_inputs.append(text_input_list.unsqueeze(0))

            encoded_inputs["text_inputs"] = torch.cat(text_inputs, dim=0)

        return encoded_inputs