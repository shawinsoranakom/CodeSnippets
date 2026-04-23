def mask_base64_data(self, msg: dict) -> dict:
        """Process the base64 image data in the message, replacing it with placeholders for easier logging

        Args:
            msg (dict): A dictionary of messages in OpenAI format

        Returns:
            dict: This is the processed message dictionary with the image data replaced with placeholders
        """
        if not isinstance(msg, dict):
            return msg

        new_msg = msg.copy()
        content = new_msg.get("content")
        img_base64_prefix = "data:image/"

        if isinstance(content, list):
            # Handling multimodal content (like gpt-4v format)
            new_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image_url":
                    image_url = item.get("image_url", {}).get("url", "")
                    if image_url.startswith(img_base64_prefix):
                        item = item.copy()
                        item["image_url"] = {"url": "<Image base64 data has been omitted>"}
                new_content.append(item)
            new_msg["content"] = new_content
        elif isinstance(content, str) and img_base64_prefix in content:
            # Process plain text messages containing base64 image data
            new_msg["content"] = "<Messages containing image base64 data have been omitted>"
        return new_msg