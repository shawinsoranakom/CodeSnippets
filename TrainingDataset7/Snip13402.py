def render(self, context):
        try:
            value = self.val_expr.resolve(context)
            max_value = self.max_expr.resolve(context)
            max_width = int(self.max_width.resolve(context))
        except VariableDoesNotExist:
            return ""
        except (ValueError, TypeError):
            raise TemplateSyntaxError("widthratio final argument must be a number")
        try:
            value = float(value)
            max_value = float(max_value)
            ratio = (value / max_value) * max_width
            result = str(round(ratio))
        except ZeroDivisionError:
            result = "0"
        except (ValueError, TypeError, OverflowError):
            result = ""

        if self.asvar:
            context[self.asvar] = result
            return ""
        else:
            return result