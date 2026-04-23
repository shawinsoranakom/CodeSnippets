def parse_pos_only(self) -> None:
        if self.fastcall:
            # positional-only, but no option groups
            # we only need one call to _PyArg_ParseStack

            self.flags = "METH_FASTCALL"
            self.parser_prototype = PARSER_PROTOTYPE_FASTCALL
            nargs = 'nargs'
            argname_fmt = 'args[%d]'
        else:
            # positional-only, but no option groups
            # we only need one call to PyArg_ParseTuple

            self.flags = "METH_VARARGS"
            self.parser_prototype = PARSER_PROTOTYPE_VARARGS
            if self.limited_capi:
                nargs = 'PyTuple_Size(args)'
                argname_fmt = 'PyTuple_GetItem(args, %d)'
            else:
                nargs = 'PyTuple_GET_SIZE(args)'
                argname_fmt = 'PyTuple_GET_ITEM(args, %d)'

        parser_code = []
        max_args = NO_VARARG if self.varpos else self.max_pos
        if self.limited_capi:
            if nargs != 'nargs':
                nargs_def = f'Py_ssize_t nargs = {nargs};'
                parser_code.append(libclinic.normalize_snippet(nargs_def, indent=4))
                nargs = 'nargs'
            if self.min_pos == max_args:
                pl = '' if self.min_pos == 1 else 's'
                parser_code.append(libclinic.normalize_snippet(f"""
                    if ({nargs} != {self.min_pos}) {{{{
                        PyErr_Format(PyExc_TypeError, "{{name}} expected {self.min_pos} argument{pl}, got %zd", {nargs});
                        goto exit;
                    }}}}
                    """,
                indent=4))
            else:
                if self.min_pos:
                    pl = '' if self.min_pos == 1 else 's'
                    parser_code.append(libclinic.normalize_snippet(f"""
                        if ({nargs} < {self.min_pos}) {{{{
                            PyErr_Format(PyExc_TypeError, "{{name}} expected at least {self.min_pos} argument{pl}, got %zd", {nargs});
                            goto exit;
                        }}}}
                        """,
                        indent=4))
                if max_args != NO_VARARG:
                    pl = '' if max_args == 1 else 's'
                    parser_code.append(libclinic.normalize_snippet(f"""
                        if ({nargs} > {max_args}) {{{{
                            PyErr_Format(PyExc_TypeError, "{{name}} expected at most {max_args} argument{pl}, got %zd", {nargs});
                            goto exit;
                        }}}}
                        """,
                    indent=4))
        elif self.min_pos or max_args != NO_VARARG:
            self.codegen.add_include('pycore_modsupport.h',
                                     '_PyArg_CheckPositional()')
            parser_code.append(libclinic.normalize_snippet(f"""
                if (!_PyArg_CheckPositional("{{name}}", {nargs}, {self.min_pos}, {max_args})) {{{{
                    goto exit;
                }}}}
                """, indent=4))

        has_optional = False
        use_parser_code = True
        for i, p in enumerate(self.parameters):
            displayname = p.get_displayname(i+1)
            argname = argname_fmt % i
            parsearg: str | None
            parsearg = p.converter.parse_arg(argname, displayname, limited_capi=self.limited_capi)
            if parsearg is None:
                if self.varpos:
                    raise ValueError(
                        f"Using converter {p.converter} is not supported "
                        f"in function with var-positional parameter")
                use_parser_code = False
                parser_code = []
                break
            if has_optional or p.is_optional():
                has_optional = True
                parser_code.append(libclinic.normalize_snippet("""
                    if (%s < %d) {{
                        goto skip_optional;
                    }}
                    """, indent=4) % (nargs, i + 1))
            parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))

        if use_parser_code:
            if has_optional:
                parser_code.append("skip_optional:")
            if self.varpos:
                parser_code.append(libclinic.normalize_snippet(self._parse_vararg(), indent=4))
            elif self.var_keyword:
                parser_code.append(libclinic.normalize_snippet(self._parse_kwarg(), indent=4))
        else:
            for parameter in self.parameters:
                parameter.converter.use_converter()

            if self.limited_capi:
                self.fastcall = False
            if self.fastcall:
                self.codegen.add_include('pycore_modsupport.h',
                                         '_PyArg_ParseStack()')
                parser_code = [libclinic.normalize_snippet("""
                    if (!_PyArg_ParseStack(args, nargs, "{format_units}:{name}",
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
            else:
                self.flags = "METH_VARARGS"
                self.parser_prototype = PARSER_PROTOTYPE_VARARGS
                parser_code = [libclinic.normalize_snippet("""
                    if (!PyArg_ParseTuple(args, "{format_units}:{name}",
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
        self.parser_body(*parser_code)