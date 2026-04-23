def render(self, context):
        if not settings.DEBUG:
            return ""

        from pprint import pformat

        output = [escape(pformat(val)) for val in context]
        output.append("\n\n")
        output.append(escape(pformat(sys.modules)))
        return "".join(output)