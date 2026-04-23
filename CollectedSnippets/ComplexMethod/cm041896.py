def parse(cls, v: str) -> "DotClassAttribute":
        """
        Parses dot format text and returns a DotClassAttribute object.

        Args:
            v (str): Dot format text to be parsed.

        Returns:
            DotClassAttribute: An instance of the DotClassAttribute class representing the parsed data.
        """
        val = ""
        meet_colon = False
        meet_equals = False
        for c in v:
            if c == ":":
                meet_colon = True
            elif c == "=":
                meet_equals = True
                if not meet_colon:
                    val += ":"
                    meet_colon = True
            val += c
        if not meet_colon:
            val += ":"
        if not meet_equals:
            val += "="

        cix = val.find(":")
        eix = val.rfind("=")
        name = val[0:cix].strip()
        type_ = val[cix + 1 : eix]
        default_ = val[eix + 1 :].strip()

        type_ = remove_white_spaces(type_)  # remove white space
        if type_ == "NoneType":
            type_ = ""
        if "Literal[" in type_:
            pre_l, literal, post_l = cls._split_literal(type_)
            composition_val = pre_l + "Literal" + post_l  # replace Literal[...] with Literal
            type_ = pre_l + literal + post_l
        else:
            type_ = re.sub(r"['\"]+", "", type_)  # remove '"
            composition_val = type_

        if default_ == "None":
            default_ = ""
        compositions = cls.parse_compositions(composition_val)
        return cls(name=name, type_=type_, default_=default_, description=v, compositions=compositions)