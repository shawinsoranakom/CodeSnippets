def _extract_sample_components(
        self, messages: List[Dict], sample_idx: int, verbose: bool
    ) -> Tuple[Optional[str], Optional[Any], Optional[str], List[Dict]]:
        """Extract ground truth, image, question, and input messages from sample."""

        # Extract system message (if present)
        system_message = next(
            (msg for msg in messages if msg["role"] == "system"), None
        )

        # Extract user message with the image and question
        user_message = next((msg for msg in messages if msg["role"] == "user"), None)
        if not user_message:
            if verbose:
                print(f"Skipping sample {sample_idx}: No user message found")
            return None, None, None, []

        # Extract assistant message with ground truth
        assistant_message = next(
            (msg for msg in messages if msg["role"] == "assistant"), None
        )
        if not assistant_message:
            if verbose:
                print(
                    f"Skipping sample {sample_idx}: No assistant message (ground truth) found"
                )
            return None, None, None, []

        # Extract ground truth text
        ground_truth = None
        for content_item in assistant_message["content"]:
            if content_item["type"] == "text":
                ground_truth = content_item["text"]
                break

        if not ground_truth:
            if verbose:
                print(
                    f"Skipping sample {sample_idx}: No text found in assistant message"
                )
            return None, None, None, []

        # Extract image and question from user message
        image = None
        question = None

        for content_item in user_message["content"]:
            if content_item["type"] == "image":
                image = content_item["image"]
            elif content_item["type"] == "text":
                question = content_item["text"]

        if not image:
            if verbose:
                print(f"Skipping sample {sample_idx}: No image found in user message")
            return None, None, None, []

        if not question:
            if verbose:
                print(
                    f"Skipping sample {sample_idx}: No question found in user message"
                )
            return None, None, None, []

        # Construct messages for the model input (excluding assistant message)
        input_messages = []
        if system_message:
            input_messages.append(system_message)
        input_messages.append(user_message)

        return ground_truth, image, question, input_messages