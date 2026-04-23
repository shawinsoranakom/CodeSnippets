def _convert_single_sample(sample):
        """Convert a single llava sample to standard VLM format."""
        messages = sample["messages"]
        images = sample.get("images", [])

        # Process each message
        new_messages = []
        for msg in messages:
            new_content = []

            for item in msg["content"]:
                if item["type"] == "image":
                    # Replace index with actual PIL image
                    if "index" in item and item["index"] is not None:
                        img_idx = item["index"]
                        if img_idx < len(images):
                            pil_image = images[img_idx]
                            # Ensure it's PIL
                            if isinstance(pil_image, str):
                                pil_image = Image.open(pil_image).convert("RGB")

                            new_content.append(
                                {
                                    "type": "image",
                                    "image": pil_image,  # Actual PIL object
                                }
                            )
                    else:
                        # No index, try to use first image
                        if len(images) > 0:
                            pil_image = images[0]
                            if isinstance(pil_image, str):
                                pil_image = Image.open(pil_image).convert("RGB")

                            new_content.append({"type": "image", "image": pil_image})

                elif item["type"] == "text":
                    # Keep text as-is (only type + text)
                    new_content.append({"type": "text", "text": item.get("text", "")})

            new_messages.append({"role": msg["role"], "content": new_content})

        return {"messages": new_messages}