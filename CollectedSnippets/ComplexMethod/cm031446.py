def validate(self):
        """Validate the input format, ensure it is the correct string formatting style"""
        fields = set()
        try:
            for _, fieldname, spec, conversion in _str_formatter.parse(self._fmt):
                if fieldname:
                    if not self.field_spec.match(fieldname):
                        raise ValueError('invalid field name/expression: %r' % fieldname)
                    fields.add(fieldname)
                if conversion and conversion not in 'rsa':
                    raise ValueError('invalid conversion: %r' % conversion)
                if spec and not self.fmt_spec.match(spec):
                    raise ValueError('bad specifier: %r' % spec)
        except ValueError as e:
            raise ValueError('invalid format: %s' % e)
        if not fields:
            raise ValueError('invalid format: no fields')