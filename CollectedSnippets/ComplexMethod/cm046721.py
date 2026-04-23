def __call__(self, batch: List[dict]) -> dict:
        """
        Collate a batch of samples.

        Args:
            batch: List of dicts, each with 'messages' containing
                   [{'role': 'user', 'content': [...]}, {'role': 'assistant', 'content': [...]}]

        Returns:
            dict with input_ids, attention_mask, labels, pixel_values, etc.
        """
        from PIL import Image

        # Extract messages and images
        all_messages = []
        all_images = []

        for sample in batch:
            messages = sample["messages"]
            all_messages.append(messages)

            # Extract PIL images from content
            for msg in messages:
                content = msg.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "image":
                            img = item.get("image")
                            if img is not None and hasattr(img, "size"):  # PIL Image
                                all_images.append(img)

        # Process with the VL processor
        try:
            # Qwen2VL style processing
            texts = [
                self.processor.apply_chat_template(
                    msgs, tokenize = False, add_generation_prompt = False
                )
                for msgs in all_messages
            ]

            # Process with images
            inputs = self.processor(
                text = texts,
                images = all_images if all_images else None,
                return_tensors = "pt",
                padding = True,
                truncation = True,
                max_length = self.max_length,
            )

            # Create labels (mask input, keep output)
            labels = inputs["input_ids"].clone()

            # Simple masking: mask padding tokens
            labels[labels == self.processor.tokenizer.pad_token_id] = self.ignore_index

            inputs["labels"] = labels

            return inputs

        except Exception as e:
            logger.info(f"⚠️ DeepSeekOCRDataCollator error: {e}")
            raise