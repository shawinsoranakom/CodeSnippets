def _complete_expression(self, text, line, begidx, endidx):
        # Complete an arbitrary expression.
        if not self.curframe:
            return []
        # Collect globals and locals.  It is usually not really sensible to also
        # complete builtins, and they clutter the namespace quite heavily, so we
        # leave them out.
        ns = {**self.curframe.f_globals, **self.curframe.f_locals}
        if '.' in text:
            # Walk an attribute chain up to the last part, similar to what
            # rlcompleter does.  This will bail if any of the parts are not
            # simple attribute access, which is what we want.
            dotted = text.split('.')
            try:
                if dotted[0].startswith('$'):
                    obj = self.curframe.f_globals['__pdb_convenience_variables'][dotted[0][1:]]
                else:
                    obj = ns[dotted[0]]
                for part in dotted[1:-1]:
                    obj = getattr(obj, part)
            except (KeyError, AttributeError):
                return []
            prefix = '.'.join(dotted[:-1]) + '.'
            return [prefix + n for n in dir(obj) if n.startswith(dotted[-1])]
        else:
            if text.startswith("$"):
                # Complete convenience variables
                conv_vars = self.curframe.f_globals.get('__pdb_convenience_variables', {})
                return [f"${name}" for name in conv_vars if name.startswith(text[1:])]
            # Complete a simple name.
            return [n for n in ns.keys() if n.startswith(text)]