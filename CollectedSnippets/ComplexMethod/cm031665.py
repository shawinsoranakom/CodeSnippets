def visit_Alt(self, node: Alt, is_loop: bool, is_gather: bool) -> None:
        has_cut = any(isinstance(item.item, Cut) for item in node.items)
        with self.local_variable_context():
            if has_cut:
                self.print("cut = False")
            if is_loop:
                self.print("while (")
            else:
                self.print("if (")
            with self.indent():
                first = True
                for item in node.items:
                    if first:
                        first = False
                    else:
                        self.print("and")
                    self.visit(item)
                    if is_gather:
                        self.print("is not None")

            self.print("):")
            with self.indent():
                action = node.action
                if not action:
                    if is_gather:
                        assert len(self.local_variable_names) == 2
                        action = (
                            f"[{self.local_variable_names[0]}] + {self.local_variable_names[1]}"
                        )
                    else:
                        if self.invalidvisitor.visit(node):
                            action = "UNREACHABLE"
                        elif len(self.local_variable_names) == 1:
                            action = f"{self.local_variable_names[0]}"
                        else:
                            action = f"[{', '.join(self.local_variable_names)}]"
                elif "LOCATIONS" in action:
                    self.print("tok = self._tokenizer.get_last_non_whitespace_token()")
                    self.print("end_lineno, end_col_offset = tok.end")
                    action = action.replace("LOCATIONS", self.location_formatting)

                if is_loop:
                    self.print(f"children.append({action})")
                    self.print("mark = self._mark()")
                else:
                    if "UNREACHABLE" in action:
                        action = action.replace("UNREACHABLE", self.unreachable_formatting)
                    self.print(f"return {action}")

            self.print("self._reset(mark)")
            # Skip remaining alternatives if a cut was reached.
            if has_cut:
                self.print("if cut: return None")