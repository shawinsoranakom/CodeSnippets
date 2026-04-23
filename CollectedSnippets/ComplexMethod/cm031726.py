def parse_argument(self, args: list[str]) -> None:
        assert not (self.converter and self.encoding)
        if self.format_unit == 'O&':
            assert self.converter
            args.append(self.converter)

        if self.encoding:
            args.append(libclinic.c_str_repr(self.encoding))
        elif self.subclass_of:
            args.append(self.subclass_of)

        s = ("&" if self.parse_by_reference else "") + self.parser_name
        args.append(s)

        if self.length:
            args.append(f"&{self.length_name}")