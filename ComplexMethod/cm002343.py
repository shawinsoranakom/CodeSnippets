def _fix_init_location(self, new_body, original_body):
        """
        Fix the location of the `super().__init__()` in the new body, if we had new statements before it.
        If the original class' `super().__init__()` is not in the beginning, do not fix it and leave where it is.
        In some cases we do not want to call super() at the very beginning.
        """
        start_index = 0
        for i, node in enumerate(original_body):
            if m.matches(node, DOCSTRING_NODE) and i == start_index:
                start_index += 1
                continue
            code = self.python_module.code_for_node(node)
            comment_less_code = re.sub(r"#.*", "", code).strip()
            comment_less_code = re.sub(r"\ *\n", "\n", comment_less_code).strip()
            if "super().__init__" in comment_less_code and i > start_index:
                return new_body

        start_index = 0
        for i, node in enumerate(new_body):
            if m.matches(node, DOCSTRING_NODE) and i == start_index:
                start_index += 1
                continue
            code = self.python_module.code_for_node(node)
            comment_less_code = re.sub(r"#.*", "", code).strip()
            comment_less_code = re.sub(r"\ *\n", "\n", comment_less_code).strip()
            if "super().__init__" in comment_less_code and i > start_index:
                # Remove it and add it again at the top after the docstrings
                node = new_body.pop(i)
                new_body = new_body[:start_index] + [node] + new_body[start_index:]
                break
        return new_body