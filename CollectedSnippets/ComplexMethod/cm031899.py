def _find(self, filename=None, funcname=None, name=None, kind=None):
        for decl in self._decls.values():
            if filename and decl.filename != filename:
                continue
            if funcname:
                if decl.kind is not KIND.VARIABLE:
                    continue
                if decl.parent.name != funcname:
                    continue
            if name and decl.name != name:
                continue
            if kind:
                kinds = KIND.resolve_group(kind)
                if decl.kind not in kinds:
                    continue
            yield decl