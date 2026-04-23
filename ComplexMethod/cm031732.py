def parse_general(self, clang: CLanguage) -> None:
        parsearg: str | None
        deprecated_positionals: dict[int, Parameter] = {}
        deprecated_keywords: dict[int, Parameter] = {}
        for i, p in enumerate(self.parameters):
            if p.deprecated_positional:
                deprecated_positionals[i] = p
            if p.deprecated_keyword:
                deprecated_keywords[i] = p

        has_optional_kw = (
            max(self.pos_only, self.min_pos) + self.min_kw_only
            < len(self.converters)
        )

        use_parser_code = True
        if self.limited_capi:
            parser_code = []
            use_parser_code = False
            self.fastcall = False
        else:
            self.codegen.add_include('pycore_modsupport.h',
                                     '_PyArg_UnpackKeywords()')
            if not self.varpos:
                nargs = "nargs"
            else:
                nargs = f"Py_MIN(nargs, {self.max_pos})" if self.max_pos else "0"

            if self.fastcall:
                self.flags = "METH_FASTCALL|METH_KEYWORDS"
                self.parser_prototype = PARSER_PROTOTYPE_FASTCALL_KEYWORDS
                self.declarations = declare_parser(self.func, codegen=self.codegen)
                self.declarations += "\nPyObject *argsbuf[%s];" % (len(self.converters) or 1)
                if self.varpos:
                    self.declarations += "\nPyObject * const *fastargs;"
                    argsname = 'fastargs'
                    argname_fmt = 'fastargs[%d]'
                else:
                    argsname = 'args'
                    argname_fmt = 'args[%d]'
                if has_optional_kw:
                    self.declarations += "\nPy_ssize_t noptargs = %s + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - %d;" % (nargs, self.min_pos + self.min_kw_only)
                unpack_args = 'args, nargs, NULL, kwnames'
            else:
                # positional-or-keyword arguments
                self.flags = "METH_VARARGS|METH_KEYWORDS"
                self.parser_prototype = PARSER_PROTOTYPE_KEYWORD
                argsname = 'fastargs'
                argname_fmt = 'fastargs[%d]'
                self.declarations = declare_parser(self.func, codegen=self.codegen)
                self.declarations += "\nPyObject *argsbuf[%s];" % (len(self.converters) or 1)
                self.declarations += "\nPyObject * const *fastargs;"
                self.declarations += "\nPy_ssize_t nargs = PyTuple_GET_SIZE(args);"
                if has_optional_kw:
                    self.declarations += "\nPy_ssize_t noptargs = %s + (kwargs ? PyDict_GET_SIZE(kwargs) : 0) - %d;" % (nargs, self.min_pos + self.min_kw_only)
                unpack_args = '_PyTuple_CAST(args)->ob_item, nargs, kwargs, NULL'
            parser_code = [libclinic.normalize_snippet(f"""
                {argsname} = _PyArg_UnpackKeywords({unpack_args}, &_parser,
                        /*minpos*/ {self.min_pos}, /*maxpos*/ {self.max_pos}, /*minkw*/ {self.min_kw_only}, /*varpos*/ {1 if self.varpos else 0}, argsbuf);
                if (!{argsname}) {{{{
                    goto exit;
                }}}}
                """, indent=4)]

        if self.requires_defining_class:
            self.flags = 'METH_METHOD|' + self.flags
            self.parser_prototype = PARSER_PROTOTYPE_DEF_CLASS

        if use_parser_code:
            if deprecated_keywords:
                code = clang.deprecate_keyword_use(self.func, deprecated_keywords,
                                                   argname_fmt,
                                                   codegen=self.codegen,
                                                   fastcall=self.fastcall)
                parser_code.append(code)

            add_label: str | None = None
            for i, p in enumerate(self.parameters):
                if isinstance(p.converter, defining_class_converter):
                    raise ValueError("defining_class should be the first "
                                    "parameter (after clang)")
                displayname = p.get_displayname(i+1)
                parsearg = p.converter.parse_arg(argname_fmt % i, displayname, limited_capi=self.limited_capi)
                if parsearg is None:
                    parser_code = []
                    use_parser_code = False
                    break
                if add_label and (i == self.pos_only or i == self.max_pos):
                    parser_code.append("%s:" % add_label)
                    add_label = None
                if not p.is_optional():
                    parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))
                elif i < self.pos_only:
                    add_label = 'skip_optional_posonly'
                    parser_code.append(libclinic.normalize_snippet("""
                        if (nargs < %d) {{
                            goto %s;
                        }}
                        """ % (i + 1, add_label), indent=4))
                    if has_optional_kw:
                        parser_code.append(libclinic.normalize_snippet("""
                            noptargs--;
                            """, indent=4))
                    parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))
                else:
                    if i < self.max_pos:
                        label = 'skip_optional_pos'
                        first_opt = max(self.min_pos, self.pos_only)
                    else:
                        label = 'skip_optional_kwonly'
                        first_opt = self.max_pos + self.min_kw_only
                    if i == first_opt:
                        add_label = label
                        parser_code.append(libclinic.normalize_snippet("""
                            if (!noptargs) {{
                                goto %s;
                            }}
                            """ % add_label, indent=4))
                    if i + 1 == len(self.parameters):
                        parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))
                    else:
                        add_label = label
                        parser_code.append(libclinic.normalize_snippet("""
                            if (%s) {{
                            """ % (argname_fmt % i), indent=4))
                        parser_code.append(libclinic.normalize_snippet(parsearg, indent=8))
                        parser_code.append(libclinic.normalize_snippet("""
                                if (!--noptargs) {{
                                    goto %s;
                                }}
                            }}
                            """ % add_label, indent=4))

        if use_parser_code:
            if add_label:
                parser_code.append("%s:" % add_label)
            if self.varpos:
                parser_code.append(libclinic.normalize_snippet(self._parse_vararg(), indent=4))
        else:
            for parameter in self.parameters:
                parameter.converter.use_converter()

            self.declarations = declare_parser(self.func, codegen=self.codegen,
                                               hasformat=True)
            if self.limited_capi:
                # positional-or-keyword arguments
                assert not self.fastcall
                self.flags = "METH_VARARGS|METH_KEYWORDS"
                self.parser_prototype = PARSER_PROTOTYPE_KEYWORD
                parser_code = [libclinic.normalize_snippet("""
                    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "{format_units}:{name}", _keywords,
                        {parse_arguments}))
                        goto exit;
                """, indent=4)]
                self.declarations = "static char *_keywords[] = {{{keywords_c} NULL}};"
                if deprecated_positionals or deprecated_keywords:
                    self.declarations += "\nPy_ssize_t nargs = PyTuple_Size(args);"

            elif self.fastcall:
                self.codegen.add_include('pycore_modsupport.h',
                                         '_PyArg_ParseStackAndKeywords()')
                parser_code = [libclinic.normalize_snippet("""
                    if (!_PyArg_ParseStackAndKeywords(args, nargs, kwnames, &_parser{parse_arguments_comma}
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
            else:
                self.codegen.add_include('pycore_modsupport.h',
                                         '_PyArg_ParseTupleAndKeywordsFast()')
                parser_code = [libclinic.normalize_snippet("""
                    if (!_PyArg_ParseTupleAndKeywordsFast(args, kwargs, &_parser,
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
                if deprecated_positionals or deprecated_keywords:
                    self.declarations += "\nPy_ssize_t nargs = PyTuple_GET_SIZE(args);"
            if deprecated_keywords:
                code = clang.deprecate_keyword_use(self.func, deprecated_keywords,
                                                   codegen=self.codegen,
                                                   fastcall=self.fastcall)
                parser_code.append(code)

        if deprecated_positionals:
            code = clang.deprecate_positional_use(self.func, deprecated_positionals)
            # Insert the deprecation code before parameter parsing.
            parser_code.insert(0, code)

        assert self.parser_prototype is not None
        self.parser_body(*parser_code, declarations=self.declarations)