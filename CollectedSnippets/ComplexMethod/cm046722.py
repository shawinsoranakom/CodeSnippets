def __call__(self, batch: List[dict]) -> dict:
        """
        Collate a batch of VLM samples.
        """
        all_messages = []
        all_images = []

        for sample in batch:
            messages = sample.get("messages", [])
            all_messages.append(messages)

            # Extract images
            for msg in messages:
                content = msg.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            img = item.get("image")
                            if img is not None:
                                all_images.append(img)

        # Apply chat template
        texts = [
            self.processor.apply_chat_template(
                msgs, tokenize = False, add_generation_prompt = False
            )
            for msgs in all_messages
        ]

        # Process inputs
        inputs = self.processor(
            text = texts,
            images = all_images if all_images else None,
            return_tensors = "pt",
            padding = True,
            truncation = True,
            max_length = self.max_length,
        )

        # Create labels
        labels = inputs["input_ids"].clone()

        # Mask padding
        if hasattr(self.processor, "tokenizer"):
            pad_token_id = self.processor.tokenizer.pad_token_id
        else:
            pad_token_id = self.processor.pad_token_id

        if pad_token_id is not None:
            labels[labels == pad_token_id] = self.ignore_index

        inputs["labels"] = labels

        return inputs