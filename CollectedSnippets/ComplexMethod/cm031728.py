def __init__(self, func: Function, codegen: CodeGen) -> None:
        self.func = func
        self.codegen = codegen

        self.parameters = list(self.func.parameters.values())
        self_parameter = self.parameters.pop(0)
        if not isinstance(self_parameter.converter, self_converter):
            raise ValueError("the first parameter must use self_converter")
        self.self_parameter_converter = self_parameter.converter

        self.requires_defining_class = False
        if self.parameters and isinstance(self.parameters[0].converter, defining_class_converter):
            self.requires_defining_class = True
            del self.parameters[0]

        for i, p in enumerate(self.parameters):
            if p.is_vararg():
                self.varpos = p
                del self.parameters[i]
                break

        for i, p in enumerate(self.parameters):
            if p.is_var_keyword():
                self.var_keyword = p
                del self.parameters[i]
                break

        self.converters = [p.converter for p in self.parameters]

        if self.func.critical_section:
            self.codegen.add_include('pycore_critical_section.h',
                                     'Py_BEGIN_CRITICAL_SECTION()')

        # Use fastcall if not disabled, except if in a __new__ or
        # __init__ method, or if there is a **kwargs parameter.
        if self.func.disable_fastcall:
            self.fastcall = False
        elif self.var_keyword is not None:
            self.fastcall = False
        else:
            self.fastcall = not self.is_new_or_init()

        self.pos_only = 0
        self.min_pos = 0
        self.max_pos = 0
        self.min_kw_only = 0
        for i, p in enumerate(self.parameters, 1):
            if p.is_keyword_only():
                assert not p.is_positional_only()
                if not p.is_optional():
                    self.min_kw_only = i - self.max_pos
            else:
                self.max_pos = i
                if p.is_positional_only():
                    self.pos_only = i
                if not p.is_optional():
                    self.min_pos = i