def visit_Alt(
        self, node: Alt, is_loop: bool, is_gather: bool, rulename: str | None
    ) -> None:
        if len(node.items) == 1 and str(node.items[0]).startswith("invalid_"):
            self.print(f"if (p->call_invalid_rules) {{ // {node}")
        else:
            self.print(f"{{ // {node}")
        with self.indent():
            self._check_for_errors()
            node_str = str(node).replace('"', '\\"')
            self.print(
                f'D(fprintf(stderr, "%*c> {rulename}[%d-%d]: %s\\n", p->level, \' \', _mark, p->mark, "{node_str}"));'
            )
            # Prepare variable declarations for the alternative
            vars = self.collect_vars(node)
            for v, var_type in sorted(item for item in vars.items() if item[0] is not None):
                if not var_type:
                    var_type = "void *"
                else:
                    var_type += " "
                if v == "_cut_var":
                    v += " = 0"  # cut_var must be initialized
                self.print(f"{var_type}{v};")
                if v and v.startswith("_opt_var"):
                    self.print(f"UNUSED({v}); // Silence compiler warnings")

            with self.local_variable_context():
                if is_loop:
                    self.handle_alt_loop(node, is_gather, rulename)
                else:
                    self.handle_alt_normal(node, is_gather, rulename)

            self.print("p->mark = _mark;")
            node_str = str(node).replace('"', '\\"')
            self.print(
                f"D(fprintf(stderr, \"%*c%s {rulename}[%d-%d]: %s failed!\\n\", p->level, ' ',\n"
                f'                  p->error_indicator ? "ERROR!" : "-", _mark, p->mark, "{node_str}"));'
            )
            if "_cut_var" in vars:
                self.print("if (_cut_var) {")
                with self.indent():
                    self.add_return("NULL")
                self.print("}")
        self.print("}")