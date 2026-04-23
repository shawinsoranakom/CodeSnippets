def as_sql(self, compiler, connection):
        param = quote_lexeme(self.value)
        label = ""
        if self.prefix:
            label += "*"
        if self.weight:
            label += self.weight

        if label:
            param = f"{param}:{label}"
        if self.invert:
            param = f"!{param}"

        return "%s", (param,)