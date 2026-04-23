def _stringify_tree(
        self,
        str_list: list[str],
        preamble: str = "",
        dir_ptr: str = "\u2500\u2500\u2500 ",
    ):
        """Recursive method to generate print-friendly version of a Directory."""
        space = "    "
        branch = "\u2502   "
        tee = "\u251c\u2500\u2500 "
        last = "\u2514\u2500\u2500 "

        # add this directory's representation
        str_list.append(f"{preamble}{dir_ptr}{self.name}\n")

        # add directory's children representations
        if dir_ptr == tee:
            preamble = preamble + branch
        else:
            preamble = preamble + space

        file_keys: list[str] = []
        dir_keys: list[str] = []
        for key, val in self.children.items():
            if val.is_dir:
                dir_keys.append(key)
            else:
                file_keys.append(key)

        for index, key in enumerate(sorted(dir_keys)):
            if (index == len(dir_keys) - 1) and len(file_keys) == 0:
                self.children[key]._stringify_tree(str_list, preamble, last)
            else:
                self.children[key]._stringify_tree(str_list, preamble, tee)
        for index, file in enumerate(sorted(file_keys)):
            pointer = last if (index == len(file_keys) - 1) else tee
            str_list.append(f"{preamble}{pointer}{file}\n")