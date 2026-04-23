def dfs(element):
            nonlocal index
            if isinstance(element, Tag):
                if element.name in self.included_tags:
                    if not self.is_excluded(element):
                        text = fast_text(element)
                        word_count = len(text.split())

                        # Headers pass through with adjusted minimum
                        if element.name in self.header_tags:
                            if word_count >= 3:  # Minimal sanity check for headers
                                candidates.append((index, text, element))
                                index += 1
                        # Regular content uses standard minimum
                        elif word_count >= self.min_word_count:
                            candidates.append((index, text, element))
                            index += 1

                for child in element.children:
                    dfs(child)