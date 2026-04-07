def create_var(self, value):
        return TemplateLiteral(self.template_parser.compile_filter(value), value)