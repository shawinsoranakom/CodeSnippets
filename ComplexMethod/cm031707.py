def parse_vararg(self, *, pos_only: int, min_pos: int, max_pos: int,
                     fastcall: bool, limited_capi: bool) -> str:
        paramname = self.parser_name
        if fastcall:
            if limited_capi:
                if min(pos_only, min_pos) < max_pos:
                    size = f'Py_MAX(nargs - {max_pos}, 0)'
                else:
                    size = f'nargs - {max_pos}' if max_pos else 'nargs'
                return f"""
                    {paramname} = PyTuple_New({size});
                    if (!{paramname}) {{{{
                        goto exit;
                    }}}}
                    for (Py_ssize_t i = {max_pos}; i < nargs; ++i) {{{{
                        PyTuple_SET_ITEM({paramname}, i - {max_pos}, Py_NewRef(args[i]));
                    }}}}
                    """
            else:
                start = f'args + {max_pos}' if max_pos else 'args'
                size = f'nargs - {max_pos}' if max_pos else 'nargs'
                if min(pos_only, min_pos) < max_pos:
                    return f"""
                        {paramname} = nargs > {max_pos}
                            ? PyTuple_FromArray({start}, {size})
                            : PyTuple_New(0);
                        if ({paramname} == NULL) {{{{
                            goto exit;
                        }}}}
                        """
                else:
                    return f"""
                        {paramname} = PyTuple_FromArray({start}, {size});
                        if ({paramname} == NULL) {{{{
                            goto exit;
                        }}}}
                        """
        else:
            if max_pos:
                return f"""
                    {paramname} = PyTuple_GetSlice(args, {max_pos}, PY_SSIZE_T_MAX);
                    if (!{paramname}) {{{{
                        goto exit;
                    }}}}
                    """
            else:
                return f"{paramname} = Py_NewRef(args);\n"