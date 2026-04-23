def modify_special_strings(self, tex: str) -> str:
        tex = tex.strip()
        should_add_filler = reduce(op.or_, [
            # Fraction line needs something to be over
            tex == "\\over",
            tex == "\\overline",
            # Makesure sqrt has overbar
            tex == "\\sqrt",
            tex == "\\sqrt{",
            # Need to add blank subscript or superscript
            tex.endswith("_"),
            tex.endswith("^"),
            tex.endswith("dot"),
        ])
        if should_add_filler:
            filler = "{\\quad}"
            tex += filler

        should_add_double_filler = reduce(op.or_, [
            tex == "\\overset",
            # TODO: these can't be used since they change
            # the latex draw order.
            # tex == "\\frac", # you can use \\over as a alternative 
            # tex == "\\dfrac",
            # tex == "\\binom",
        ])
        if should_add_double_filler:
            filler = "{\\quad}{\\quad}"
            tex += filler

        if tex == "\\substack":
            tex = "\\quad"

        if tex == "":
            tex = "\\quad"

        # To keep files from starting with a line break
        if tex.startswith("\\\\"):
            tex = tex.replace("\\\\", "\\quad\\\\")

        tex = self.balance_braces(tex)

        # Handle imbalanced \left and \right
        num_lefts, num_rights = [
            len([
                s for s in tex.split(substr)[1:]
                if s and s[0] in "(){}[]|.\\"
            ])
            for substr in ("\\left", "\\right")
        ]
        if num_lefts != num_rights:
            tex = tex.replace("\\left", "\\big")
            tex = tex.replace("\\right", "\\big")

        for context in ["array"]:
            begin_in = ("\\begin{%s}" % context) in tex
            end_in = ("\\end{%s}" % context) in tex
            if begin_in ^ end_in:
                # Just turn this into a blank string,
                # which means caller should leave a
                # stray \\begin{...} with other symbols
                tex = ""
        return tex