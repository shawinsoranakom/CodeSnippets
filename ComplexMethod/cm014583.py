def parse(src: object) -> Precompute:
        if not isinstance(src, list):
            raise AssertionError(f"precomputed must be a list, got {type(src)}")

        # src is a list of strings of the format:
        #   {kernel param name} -> {replacement decl}[, {replacement decl}, ...]
        #   [{add decl}[, {add decl}, ...]]
        # The last line is optional and contains the precomputed parameters that are
        # added without replacement.
        # The other lines are parsed to get the names of which precomputed elements
        # should replace which kernel arguments.
        add_args = []
        if " -> " not in src[-1]:
            add_list = src[-1].split(",")
            add_args = [Argument.parse(name.strip()) for name in add_list]
            src = src[:-1]

        replace = {}
        for raw_replace_item in src:
            if not isinstance(raw_replace_item, str):
                raise AssertionError(
                    f"precomputed item must be a str, got {type(raw_replace_item)}"
                )
            if " -> " not in raw_replace_item:
                raise AssertionError(
                    f"precomputed parameters without replacement are allowed only in the last line, got: {raw_replace_item}"
                )

            arg, with_list_raw = raw_replace_item.split(" -> ")
            if " " in arg:
                raise AssertionError(
                    f"illegal kernel param name '{arg}' in precomputed parameters"
                )
            with_list = with_list_raw.split(",")
            with_list_args = [Argument.parse(name.strip()) for name in with_list]
            replace[arg] = with_list_args

        r = Precompute(replace=replace, add=add_args)
        if r.to_list() != src:
            raise AssertionError(f"r.to_list() != src: {r.to_list()} != {src}")
        return r