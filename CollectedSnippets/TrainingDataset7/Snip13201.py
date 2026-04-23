def resolve(self, context, ignore_failures=False):
        if self.is_var:
            try:
                obj = self.var.resolve(context)
            except VariableDoesNotExist:
                if ignore_failures:
                    obj = None
                else:
                    string_if_invalid = context.template.engine.string_if_invalid
                    if string_if_invalid:
                        if "%s" in string_if_invalid:
                            return string_if_invalid % self.var
                        else:
                            return string_if_invalid
                    else:
                        obj = string_if_invalid
        else:
            obj = self.var
        for func, args in self.filters:
            arg_vals = []
            for lookup, arg in args:
                if not lookup:
                    arg_vals.append(mark_safe(arg))
                else:
                    arg_vals.append(arg.resolve(context))
            if getattr(func, "expects_localtime", False):
                obj = template_localtime(obj, context.use_tz)
            if getattr(func, "needs_autoescape", False):
                new_obj = func(obj, autoescape=context.autoescape, *arg_vals)
            else:
                new_obj = func(obj, *arg_vals)
            if getattr(func, "is_safe", False) and isinstance(obj, SafeData):
                obj = mark_safe(new_obj)
            else:
                obj = new_obj
        return obj