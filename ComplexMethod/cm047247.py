def format(self, percent: str, value, grouping: bool = False) -> str:
        """ Format() will return the language-specific output for float values"""
        self.ensure_one()
        if percent[0] != '%':
            raise ValueError(_("format() must be given exactly one %char format specifier"))

        formatted = percent % value

        data = self._get_data(id=self.id)
        if not data:
            raise UserError(_("The language %s is not installed.", self.name))
        decimal_point = data.decimal_point
        # floats and decimal ints need special action!
        if grouping:
            lang_grouping, thousands_sep = data.grouping, data.thousands_sep or ''
            eval_lang_grouping = ast.literal_eval(lang_grouping)

            if percent[-1] in 'eEfFgG':
                parts = formatted.split('.')
                parts[0] = intersperse(parts[0], eval_lang_grouping, thousands_sep)[0]

                formatted = decimal_point.join(parts)

            elif percent[-1] in 'diu':
                formatted = intersperse(formatted, eval_lang_grouping, thousands_sep)[0]

        elif percent[-1] in 'eEfFgG' and '.' in formatted:
            formatted = formatted.replace('.', decimal_point)

        return formatted