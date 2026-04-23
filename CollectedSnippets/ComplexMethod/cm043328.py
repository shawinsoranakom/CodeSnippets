def extract_text_chunks(
        self, body: Tag, min_word_threshold: int = None
    ) -> List[Tuple[str, str]]:
        """
        Extracts text chunks from a BeautifulSoup body element while preserving order.
        Returns list of tuples (text, tag_name) for classification.

        Args:
            body: BeautifulSoup Tag object representing the body element

        Returns:
            List of (text, tag_name) tuples
        """
        # Tags to ignore - inline elements that shouldn't break text flow
        INLINE_TAGS = {
            "a",
            "abbr",
            "acronym",
            "b",
            "bdo",
            "big",
            "br",
            "button",
            "cite",
            "code",
            "dfn",
            "em",
            "i",
            "img",
            "input",
            "kbd",
            "label",
            "map",
            "object",
            "q",
            "samp",
            "script",
            "select",
            "small",
            "span",
            "strong",
            "sub",
            "sup",
            "textarea",
            "time",
            "tt",
            "var",
        }

        # Tags that typically contain meaningful headers
        HEADER_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "header"}

        chunks = []
        current_text = []
        chunk_index = 0

        def should_break_chunk(tag: Tag) -> bool:
            """Determine if a tag should cause a break in the current text chunk"""
            return tag.name not in INLINE_TAGS and not (
                tag.name == "p" and len(current_text) == 0
            )

        # Use deque for efficient push/pop operations
        stack = deque([(body, False)])

        while stack:
            element, visited = stack.pop()

            if visited:
                # End of block element - flush accumulated text
                if current_text and should_break_chunk(element):
                    text = " ".join("".join(current_text).split())
                    if text:
                        tag_type = (
                            "header" if element.name in HEADER_TAGS else "content"
                        )
                        chunks.append((chunk_index, text, tag_type, element))
                        chunk_index += 1
                    current_text = []
                continue

            if isinstance(element, NavigableString):
                if str(element).strip():
                    current_text.append(str(element).strip())
                continue

            # Pre-allocate children to avoid multiple list operations
            children = list(element.children)
            if not children:
                continue

            # Mark block for revisit after processing children
            stack.append((element, True))

            # Add children in reverse order for correct processing
            for child in reversed(children):
                if isinstance(child, (Tag, NavigableString)):
                    stack.append((child, False))

        # Handle any remaining text
        if current_text:
            text = " ".join("".join(current_text).split())
            if text:
                chunks.append((chunk_index, text, "content", body))

        if min_word_threshold:
            chunks = [
                chunk for chunk in chunks if len(chunk[1].split()) >= min_word_threshold
            ]

        return chunks