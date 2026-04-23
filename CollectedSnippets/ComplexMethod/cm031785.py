def generate_unicode(self, name: str, s: str) -> str:
        if s in self.strings:
            return f"&_Py_STR({self.strings[s]})"
        if s in self.identifiers:
            return f"&_Py_ID({s})"
        if len(s) == 1:
            c = ord(s)
            if c < 128:
                return f"(PyObject *)&_Py_SINGLETON(strings).ascii[{c}]"
            elif c < 256:
                return f"(PyObject *)&_Py_SINGLETON(strings).latin1[{c - 128}]"
        if re.match(r'\A[A-Za-z0-9_]+\Z', s):
            name = f"const_str_{s}"
        kind, ascii = analyze_character_width(s)
        if kind == PyUnicode_1BYTE_KIND:
            datatype = "uint8_t"
        elif kind == PyUnicode_2BYTE_KIND:
            datatype = "uint16_t"
        else:
            datatype = "uint32_t"
        self.write("static")
        with self.indent():
            with self.block("struct"):
                if ascii:
                    self.write("PyASCIIObject _ascii;")
                else:
                    self.write("PyCompactUnicodeObject _compact;")
                self.write(f"{datatype} _data[{len(s)+1}];")
        with self.block(f"{name} =", ";"):
            if ascii:
                with self.block("._ascii =", ","):
                    self.object_head("PyUnicode_Type")
                    self.write(f".length = {len(s)},")
                    self.write(".hash = -1,")
                    with self.block(".state =", ","):
                        self.write(".kind = 1,")
                        self.write(".compact = 1,")
                        self.write(".ascii = 1,")
                        self.write(".statically_allocated = 1,")
                self.write(f"._data = {make_string_literal(s.encode('ascii'))},")
                return f"& {name}._ascii.ob_base"
            else:
                with self.block("._compact =", ","):
                    with self.block("._base =", ","):
                        self.object_head("PyUnicode_Type")
                        self.write(f".length = {len(s)},")
                        self.write(".hash = -1,")
                        with self.block(".state =", ","):
                            self.write(f".kind = {kind},")
                            self.write(".compact = 1,")
                            self.write(".ascii = 0,")
                            self.write(".statically_allocated = 1,")
                    utf8 = s.encode('utf-8')
                    self.write(f'.utf8 = {make_string_literal(utf8)},')
                    self.write(f'.utf8_length = {len(utf8)},')
                with self.block(f"._data =", ","):
                    for i in range(0, len(s), 16):
                        data = s[i:i+16]
                        self.write(", ".join(map(str, map(ord, data))) + ",")
                return f"& {name}._compact._base.ob_base"