def _extend(self, decls):
        decls = iter(decls)
        # Check only the first item.
        for decl in decls:
            if isinstance(decl, Declaration):
                self._add_decl(decl)
                # Add the rest without checking.
                for decl in decls:
                    self._add_decl(decl)
            elif isinstance(decl, HighlevelParsedItem):
                raise NotImplementedError(decl)
            else:
                try:
                    key, decl = decl
                except ValueError:
                    raise NotImplementedError(decl)
                if not isinstance(decl, Declaration):
                    raise NotImplementedError(decl)
                self._add_decl(decl, key)
                # Add the rest without checking.
                for key, decl in decls:
                    self._add_decl(decl, key)