async def _walk_for_body(self, part, msg_id, service, depth=0):
        """Recursively walk through email parts to find readable body content."""
        # Prevent infinite recursion by limiting depth
        if depth > 10:
            return None

        mime_type = part.get("mimeType", "")
        body = part.get("body", {})

        # Handle text/plain content
        if mime_type == "text/plain" and body.get("data"):
            return self._decode_base64(body["data"])

        # Handle text/html content (convert to plain text)
        if mime_type == "text/html" and body.get("data"):
            html_content = self._decode_base64(body["data"])
            if html_content:
                try:
                    import html2text

                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    h.ignore_images = True
                    return h.handle(html_content)
                except Exception:
                    # Keep extraction resilient if html2text is unavailable or fails.
                    return html_content

        # Handle content stored as attachment
        if body.get("attachmentId"):
            attachment_data = await self._download_attachment_body(
                body["attachmentId"], msg_id, service
            )
            if attachment_data:
                return self._decode_base64(attachment_data)

        # Recursively search in parts
        for sub_part in part.get("parts", []):
            text = await self._walk_for_body(sub_part, msg_id, service, depth + 1)
            if text:
                return text

        return None