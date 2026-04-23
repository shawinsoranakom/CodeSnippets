def parse(cls, style_definition: str) -> "Style":
        """Parse a style definition.

        Args:
            style_definition (str): A string containing a style.

        Raises:
            errors.StyleSyntaxError: If the style definition syntax is invalid.

        Returns:
            `Style`: A Style instance.
        """
        if style_definition.strip() == "none" or not style_definition:
            return cls.null()

        STYLE_ATTRIBUTES = cls.STYLE_ATTRIBUTES
        color: Optional[str] = None
        bgcolor: Optional[str] = None
        attributes: Dict[str, Optional[Any]] = {}
        link: Optional[str] = None

        words = iter(style_definition.split())
        for original_word in words:
            word = original_word.lower()
            if word == "on":
                word = next(words, "")
                if not word:
                    raise errors.StyleSyntaxError("color expected after 'on'")
                try:
                    Color.parse(word)
                except ColorParseError as error:
                    raise errors.StyleSyntaxError(
                        f"unable to parse {word!r} as background color; {error}"
                    ) from None
                bgcolor = word

            elif word == "not":
                word = next(words, "")
                attribute = STYLE_ATTRIBUTES.get(word)
                if attribute is None:
                    raise errors.StyleSyntaxError(
                        f"expected style attribute after 'not', found {word!r}"
                    )
                attributes[attribute] = False

            elif word == "link":
                word = next(words, "")
                if not word:
                    raise errors.StyleSyntaxError("URL expected after 'link'")
                link = word

            elif word in STYLE_ATTRIBUTES:
                attributes[STYLE_ATTRIBUTES[word]] = True

            else:
                try:
                    Color.parse(word)
                except ColorParseError as error:
                    raise errors.StyleSyntaxError(
                        f"unable to parse {word!r} as color; {error}"
                    ) from None
                color = word
        style = Style(color=color, bgcolor=bgcolor, link=link, **attributes)
        return style