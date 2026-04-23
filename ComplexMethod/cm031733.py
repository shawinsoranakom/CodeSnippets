def process_methoddef(self, clang: CLanguage) -> None:
        methoddef_cast_end = ""
        if self.flags in ('METH_NOARGS', 'METH_O', 'METH_VARARGS'):
            methoddef_cast = "(PyCFunction)"
        elif self.func.kind is GETTER:
            methoddef_cast = "" # This should end up unused
        elif self.limited_capi:
            methoddef_cast = "(PyCFunction)(void(*)(void))"
        else:
            methoddef_cast = "_PyCFunction_CAST("
            methoddef_cast_end = ")"

        if self.func.methoddef_flags:
            self.flags += '|' + self.func.methoddef_flags

        self.methoddef_define = self.methoddef_define.replace('{methoddef_flags}', self.flags)
        self.methoddef_define = self.methoddef_define.replace('{methoddef_cast}', methoddef_cast)
        self.methoddef_define = self.methoddef_define.replace('{methoddef_cast_end}', methoddef_cast_end)

        self.methoddef_ifndef = ''
        conditional = clang.cpp.condition()
        if not conditional:
            self.cpp_if = self.cpp_endif = ''
        else:
            self.cpp_if = "#if " + conditional
            self.cpp_endif = "#endif /* " + conditional + " */"

            if self.methoddef_define and self.codegen.add_ifndef_symbol(self.func.full_name):
                self.methoddef_ifndef = METHODDEF_PROTOTYPE_IFNDEF