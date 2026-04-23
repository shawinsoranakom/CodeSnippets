def _parse_args(v: str) -> List[DotClassAttribute]:
        """
        Parses the dot format method arguments part and returns the parsed arguments.

        Args:
            v (str): The dot format text containing the arguments part to be parsed.

        Returns:
            str: The parsed method arguments.
        """
        if not v:
            return []
        parts = []
        bix = 0
        counter = 0
        for i in range(0, len(v)):
            c = v[i]
            if c == "[":
                counter += 1
                continue
            elif c == "]":
                counter -= 1
                continue
            elif c == "," and counter == 0:
                parts.append(v[bix:i].strip())
                bix = i + 1
        parts.append(v[bix:].strip())

        attrs = []
        for p in parts:
            if p:
                attr = DotClassAttribute.parse(p)
                attrs.append(attr)
        return attrs