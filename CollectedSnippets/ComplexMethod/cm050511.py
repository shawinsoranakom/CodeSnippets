def _check_pattern(self):
        for rule in self:
            p = rule.pattern.replace('\\\\', 'X').replace('\\{', 'X').replace('\\}', 'X')
            findall = re.findall("[{]|[}]", p)  # p does not contain escaped { or }
            if len(findall) == 2:
                if not re.search("[{][N]*[D]*[}]", p):
                    raise ValidationError(_("There is a syntax error in the barcode pattern %(pattern)s: braces can only contain N's followed by D's.", pattern=rule.pattern))
                elif re.search("[{][}]", p):
                    raise ValidationError(_("There is a syntax error in the barcode pattern %(pattern)s: empty braces.", pattern=rule.pattern))
            elif len(findall) != 0:
                raise ValidationError(_("There is a syntax error in the barcode pattern %(pattern)s: a rule can only contain one pair of braces.", pattern=rule.pattern))
            elif p == '*':
                raise ValidationError(_(" '*' is not a valid Regex Barcode Pattern. Did you mean '.*'?"))
            try:
                re.compile(re.sub('{N+D*}', '', p))
            except re.error:
                raise ValidationError(_("The barcode pattern %(pattern)s does not lead to a valid regular expression.", pattern=rule.pattern))