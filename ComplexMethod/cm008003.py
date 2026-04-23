def _format_text(self, handle, allow_colors, text, f, fallback=None, *, test_encoding=False):
        text = str(text)
        if test_encoding:
            original_text = text
            # handle.encoding can be None. See https://github.com/yt-dlp/yt-dlp/issues/2711
            encoding = self.params.get('encoding') or getattr(handle, 'encoding', None) or 'ascii'
            text = text.encode(encoding, 'ignore').decode(encoding)
            if fallback is not None and text != original_text:
                text = fallback
        return format_text(text, f) if allow_colors is True else text if fallback is None else fallback