async def _summarize(self, text: str, max_words=200, keep_language: bool = False, limit: int = -1) -> str:
        max_token_count = DEFAULT_MAX_TOKENS
        max_count = 100
        text_length = len(text)
        if limit > 0 and text_length < limit:
            return text
        summary = ""
        while max_count > 0:
            if text_length < max_token_count:
                summary = await self._get_summary(text=text, max_words=max_words, keep_language=keep_language)
                break

            padding_size = 20 if max_token_count > 20 else 0
            text_windows = self.split_texts(text, window_size=max_token_count - padding_size)
            part_max_words = min(int(max_words / len(text_windows)) + 1, 100)
            summaries = []
            for ws in text_windows:
                response = await self._get_summary(text=ws, max_words=part_max_words, keep_language=keep_language)
                summaries.append(response)
            if len(summaries) == 1:
                summary = summaries[0]
                break

            # Merged and retry
            text = "\n".join(summaries)
            text_length = len(text)

            max_count -= 1  # safeguard
        return summary