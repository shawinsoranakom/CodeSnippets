def _validate_tokens(tokens: list[Token]) -> None:
        """Ensure the XML has a single root element and no stray text."""
        if not tokens:
            raise ValueError("XML input is empty.")

        depth = 0
        root_seen = False

        for token in tokens:
            if token.type == "TAG_OPEN":
                if depth == 0 and root_seen:
                    raise ValueError("XML must have a single root element.")
                depth += 1
                if depth == 1:
                    root_seen = True
            elif token.type == "TAG_CLOSE":
                depth -= 1
                if depth < 0:
                    raise ValueError("Unexpected closing tag in XML input.")
            elif token.type in {"TEXT", "ESCAPE"}:
                if depth == 0 and token.value:
                    raise ValueError(
                        "XML contains text outside the root element; "
                        "wrap content in a single root tag."
                    )

        if depth != 0:
            raise ValueError("Unclosed tag detected in XML input.")
        if not root_seen:
            raise ValueError("XML must include a root element.")