def add_env(self, decl, insertafter=None, insertbefore=None):
        if not (insertafter or insertbefore):
            self.lines.insert(0, decl)
            return

        if insertafter:
            other_name = insertafter
        elif insertbefore:
            other_name = insertbefore
        other_decl = self.find_env(other_name)
        if len(other_decl) > 0:
            if insertafter:
                index = other_decl[0] + 1
            elif insertbefore:
                index = other_decl[0]
            self.lines.insert(index, decl)
            return

        self.module.fail_json(msg="Variable named '%s' not found." % other_name)