def _handle_loop_rule_body(self, node: Rule, rhs: Rhs) -> None:
        memoize = self._should_memoize(node)
        is_repeat1 = node.name.startswith("_loop1")

        with self.indent():
            self.add_level()
            self._check_for_errors()
            self.print("void *_res = NULL;")
            if memoize:
                self.print(f"if (_PyPegen_is_memoized(p, {node.name}_type, &_res)) {{")
                with self.indent():
                    self.add_return("_res")
                self.print("}")
            self.print("int _mark = p->mark;")
            if memoize:
                self.print("int _start_mark = p->mark;")
            self.print("void **_children = PyMem_Malloc(sizeof(void *));")
            self.out_of_memory_return("!_children")
            self.print("Py_ssize_t _children_capacity = 1;")
            self.print("Py_ssize_t _n = 0;")
            if any(alt.action and "EXTRA" in alt.action for alt in rhs.alts):
                self._set_up_token_start_metadata_extraction()
            self.visit(
                rhs,
                is_loop=True,
                is_gather=node.is_gather(),
                rulename=node.name,
            )
            if is_repeat1:
                self.print("if (_n == 0 || p->error_indicator) {")
                with self.indent():
                    self.print("PyMem_Free(_children);")
                    self.add_return("NULL")
                self.print("}")
            self.print("asdl_seq *_seq = (asdl_seq*)_Py_asdl_generic_seq_new(_n, p->arena);")
            self.out_of_memory_return("!_seq", cleanup_code="PyMem_Free(_children);")
            self.print("for (Py_ssize_t i = 0; i < _n; i++) asdl_seq_SET_UNTYPED(_seq, i, _children[i]);")
            self.print("PyMem_Free(_children);")
            if memoize and node.name:
                self.print(f"_PyPegen_insert_memo(p, _start_mark, {node.name}_type, _seq);")
            self.add_return("_seq")