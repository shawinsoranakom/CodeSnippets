def parse_args(self, clang: CLanguage) -> dict[str, str]:
        self.select_prototypes()
        self.init_limited_capi()

        self.flags = ""
        self.declarations = ""
        self.parser_prototype = ""
        self.parser_definition = ""
        self.impl_prototype = None
        self.impl_definition = IMPL_DEFINITION_PROTOTYPE

        # parser_body_fields remembers the fields passed in to the
        # previous call to parser_body. this is used for an awful hack.
        self.parser_body_fields: tuple[str, ...] = ()

        if not self.parameters and not self.varpos and not self.var_keyword:
            self.parse_no_args()
        elif self.use_meth_o():
            self.parse_one_arg()
        elif self.has_option_groups():
            self.parse_option_groups()
        elif self.var_keyword is not None:
            self.parse_var_keyword()
        elif (not self.requires_defining_class
              and self.pos_only == len(self.parameters)):
            self.parse_pos_only()
        else:
            self.parse_general(clang)

        self.copy_includes()
        if self.is_new_or_init():
            self.handle_new_or_init()
        self.process_methoddef(clang)
        self.finalize(clang)

        return self.create_template_dict()