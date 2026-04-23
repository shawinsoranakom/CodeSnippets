def interpret_statement(self, stmt, local_vars, allow_recursion, *args, **kwargs):
            if cls.ENABLED and stmt.strip():
                cls.write(stmt, level=allow_recursion)
            try:
                ret, should_ret = f(self, stmt, local_vars, allow_recursion, *args, **kwargs)
            except Exception as e:
                if cls.ENABLED:
                    if isinstance(e, ExtractorError):
                        e = e.orig_msg
                    cls.write('=> Raises:', e, '<-|', stmt, level=allow_recursion)
                raise
            if cls.ENABLED and stmt.strip():
                if should_ret or repr(ret) != stmt:
                    cls.write(['->', '=>'][bool(should_ret)], repr(ret), '<-|', stmt, level=allow_recursion)
            return ret, should_ret