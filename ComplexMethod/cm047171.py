def visit_Call(self, node: ast.Call):
        value = None
        match node.func, node.args, node.keywords:
            case ast.Name(id='context_today'), [], []:
                return "now"
            case ast.Attribute(value=ast.Attribute(value=ast.Name(id='datetime'), attr='datetime'), attr='now'), [], []:
                return "now"
            case ast.Attribute(value=value_node, attr='to_utc'), [], []:
                value = self.visit(value_node)
            case ast.Attribute(value=value, attr='strftime'), [ast.Constant(value=format)], _:
                if isinstance(value, ast.Name) and value.id == 'time':
                    # time.strftime is sometimes called directly
                    value = "now"
                else:
                    value = self.visit(value)
                if isinstance(value, str):
                    if len(format) <= 10:
                        value = value.replace('now', 'today')
                    if '-01' in format:  # some people format the date by setting day to 1
                        value += ' =1d'
            case ast.Name(id='relativedelta'), [], kws:
                value = self.parse_offset_keywords(kws)
            case ast.Attribute(value=ast.Name(id='datetime'), attr='timedelta'), [], kws:
                value = self.parse_offset_keywords(kws)
            case (ast.Attribute(value=ast.Name(id='datetime'), attr='timedelta'), [const], []) if isinstance(const, ast.Constant):
                value = self.parse_offset_keywords([ast.keyword('days', const)])
            case ast.Attribute(value=ast.Attribute(value=ast.Name(id='datetime'), attr='datetime'), attr='combine'), [value_node, time_node], []:
                value = self.visit(value_node)
                time_value = self.visit(time_node)
                if isinstance(value, str) and isinstance(time_value, datetime.time):
                    if time_value == datetime.time.min:
                        return value.replace('now', 'today')
                    if time_value == datetime.time(23, 59, 59):
                        return value.replace('now', 'today') + " +1d!"
                return self._cannot_parse(node, "call_combine")
            case ast.Attribute(value=ast.Name(id='datetime'), attr='time'), args, []:
                with contextlib.suppress(ValueError):
                    return datetime.time(*(n.value for n in args))

        if isinstance(value, str):
            return value
        return self._cannot_parse(node, "call")