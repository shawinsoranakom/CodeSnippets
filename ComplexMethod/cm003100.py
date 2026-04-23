def __call__(self, text=None, sequence=None, image_size=None, parse_tasks=None) -> dict[str, Any]:
        """
        Process model output and parse into task-specific results.

        Args:
            text (`Optional[str]`, *optional*):
                Generated text. Either this or `sequence` must be provided.
            sequence (`Optional[Union[list[int], torch.Tensor]]`, *optional*):
                Token sequence. Either this or `text` must be provided.
            image_size (`Optional[tuple[int, int]]`, *optional*):
                Image size (width, height) required for dequantization.
            parse_tasks (`Optional[Union[str, list[str]]]`, *optional*):
                Specific tasks to parse. If None, parse all supported tasks.

        Returns:
            `dict[str, Any]`: Parsed results for each task, including the raw 'text'.
        """
        if parse_tasks is not None:
            parse_tasks = [parse_tasks] if isinstance(parse_tasks, str) else parse_tasks
            for task in parse_tasks:
                if task not in self.parse_task_config.keys():
                    raise ValueError(f"Unsupported parse task: {task}")

        if (text is None and sequence is None) or (text is not None and sequence is not None):
            raise ValueError("Exactly one of 'text' or 'sequence' must be provided.")

        if sequence is not None:
            if isinstance(sequence, torch.Tensor):
                sequence = sequence.tolist()
            sequence = sequence[1:] if sequence[0] == self.tokenizer.bos_token_id else sequence  # Skip BOS if present
            text, _ = self.decode_with_spans(sequence)

        parsed_dict = {"text": text}

        tasks_to_parse = parse_tasks or self.parse_task_config.keys()
        for task in tasks_to_parse:
            config = self.parse_task_config[task]
            pattern = config.get("PATTERN")

            if task == "ocr":
                parsed_dict["ocr"] = self.parse_ocr_from_text_and_spans(
                    text, pattern=pattern, image_size=image_size, area_threshold=config.get("AREA_THRESHOLD", 0.0)
                )
            elif task == "phrase_grounding":
                parsed_dict["phrase_grounding"] = self.parse_phrase_grounding_from_text_and_spans(
                    text, image_size=image_size
                )
            elif task == "pure_text":
                parsed_dict["pure_text"] = text
            elif task == "description_with_bboxes":
                parsed_dict["description_with_bboxes"] = self.parse_description_with_bboxes_from_text_and_spans(
                    text, image_size=image_size
                )
            elif task == "description_with_polygons":
                parsed_dict["description_with_polygons"] = self.parse_description_with_polygons_from_text_and_spans(
                    text, image_size=image_size
                )
            elif task == "polygons":
                parsed_dict["polygons"] = self.parse_description_with_polygons_from_text_and_spans(
                    text, image_size=image_size, allow_empty_phrase=True
                )
            elif task == "bboxes":
                parsed_dict["bboxes"] = self.parse_description_with_bboxes_from_text_and_spans(
                    text, image_size=image_size, allow_empty_phrase=True
                )
            elif task == "description_with_bboxes_or_polygons":
                if "<poly>" in text:
                    instances = self.parse_description_with_polygons_from_text_and_spans(text, image_size=image_size)
                else:
                    instances = self.parse_description_with_bboxes_from_text_and_spans(text, image_size=image_size)
                parsed_dict["description_with_bboxes_or_polygons"] = instances
            else:
                raise ValueError(f"task {task} is not supported")

        return parsed_dict