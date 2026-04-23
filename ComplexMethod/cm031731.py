def parse_var_keyword(self) -> None:
        self.flags = "METH_VARARGS|METH_KEYWORDS"
        self.parser_prototype = PARSER_PROTOTYPE_KEYWORD
        nargs = 'PyTuple_GET_SIZE(args)'

        parser_code = []
        max_args = NO_VARARG if self.varpos else self.max_pos
        if self.varpos is None and self.min_pos == self.max_pos == 0:
            self.codegen.add_include('pycore_modsupport.h',
                                     '_PyArg_NoPositional()')
            parser_code.append(libclinic.normalize_snippet("""
                if (!_PyArg_NoPositional("{name}", args)) {{
                    goto exit;
                }}
                """, indent=4))
        elif self.min_pos or max_args != NO_VARARG:
            self.codegen.add_include('pycore_modsupport.h',
                                     '_PyArg_CheckPositional()')
            parser_code.append(libclinic.normalize_snippet(f"""
                if (!_PyArg_CheckPositional("{{name}}", {nargs}, {self.min_pos}, {max_args})) {{{{
                    goto exit;
                }}}}
                """, indent=4))

        for i, p in enumerate(self.parameters):
            parse_arg = p.converter.parse_arg(
                f'PyTuple_GET_ITEM(args, {i})',
                p.get_displayname(i+1),
                limited_capi=self.limited_capi,
            )
            assert parse_arg is not None
            parser_code.append(libclinic.normalize_snippet(parse_arg, indent=4))

        if self.varpos:
            parser_code.append(libclinic.normalize_snippet(self._parse_vararg(), indent=4))
        if self.var_keyword:
            parser_code.append(libclinic.normalize_snippet(self._parse_kwarg(), indent=4))
        self.parser_body(*parser_code)