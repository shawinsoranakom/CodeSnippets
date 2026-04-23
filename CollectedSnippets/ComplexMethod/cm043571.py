def get_completions(
        self,
        document: Document,
        _complete_event: CompleteEvent,
    ) -> Iterable[Completion]:
        """Get completions."""
        # Get list of words.
        words = self.words
        if callable(words):
            words = words()

        # Get word/text before cursor.
        if self.sentence:
            word_before_cursor = document.text_before_cursor
        else:
            word_before_cursor = document.get_word_before_cursor(
                WORD=self.WORD, pattern=self.pattern
            )
            if (
                "--" in document.text_before_cursor
                and document.text_before_cursor.rfind(" --")
                >= document.text_before_cursor.rfind(" -")
            ):
                word_before_cursor = f"--{document.text_before_cursor.split('--')[-1]}"
            elif f"--{word_before_cursor}" == document.text_before_cursor:
                word_before_cursor = document.text_before_cursor

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        def word_matches(word: str) -> bool:
            """Set True when the word before the cursor matches."""
            if self.ignore_case:
                word = word.lower()

            if self.match_middle:
                return word_before_cursor in word
            return word.startswith(word_before_cursor)

        for a in words:
            if word_matches(a):
                display = self.display_dict.get(a, a)
                display_meta = self.meta_dict.get(a, "")
                yield Completion(
                    text=a,
                    start_position=-len(word_before_cursor),
                    display=display,
                    display_meta=display_meta,
                )