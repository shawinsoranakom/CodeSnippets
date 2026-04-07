def trim_punctuation(self, word):
        """
        Trim trailing and wrapping punctuation from `word`. Return the items of
        the new state.
        """
        # Strip all opening wrapping punctuation.
        middle = word.lstrip(self.wrapping_punctuation_openings)
        lead = word[: len(word) - len(middle)]
        trail = deque()

        # Continue trimming until middle remains unchanged.
        trimmed_something = True
        counts = CountsDict(word=middle)
        while trimmed_something and middle:
            trimmed_something = False
            # Trim wrapping punctuation.
            for opening, closing in self.wrapping_punctuation:
                if counts[opening] < counts[closing]:
                    rstripped = middle.rstrip(closing)
                    if rstripped != middle:
                        strip = counts[closing] - counts[opening]
                        trail.appendleft(middle[-strip:])
                        middle = middle[:-strip]
                        trimmed_something = True
                        counts[closing] -= strip

            amp = middle.rfind("&")
            if amp == -1:
                rstripped = middle.rstrip(self.trailing_punctuation_chars)
            else:
                rstripped = middle.rstrip(self.trailing_punctuation_chars_no_semicolon)
            if rstripped != middle:
                trail.appendleft(middle[len(rstripped) :])
                middle = rstripped
                trimmed_something = True

            if self.trailing_punctuation_chars_has_semicolon and middle.endswith(";"):
                # Only strip if not part of an HTML entity.
                potential_entity = middle[amp:]
                escaped = html.unescape(potential_entity)
                if escaped == potential_entity or escaped.endswith(";"):
                    rstripped = middle.rstrip(self.trailing_punctuation_chars)
                    trail_start = len(rstripped)
                    amount_trailing_semicolons = len(middle) - len(middle.rstrip(";"))
                    if amp > -1 and amount_trailing_semicolons > 1:
                        # Leave up to most recent semicolon as might be an
                        # entity.
                        recent_semicolon = middle[trail_start:].index(";")
                        middle_semicolon_index = recent_semicolon + trail_start + 1
                        trail.appendleft(middle[middle_semicolon_index:])
                        middle = rstripped + middle[trail_start:middle_semicolon_index]
                    else:
                        trail.appendleft(middle[trail_start:])
                        middle = rstripped
                    trimmed_something = True

        trail = "".join(trail)
        return lead, middle, trail