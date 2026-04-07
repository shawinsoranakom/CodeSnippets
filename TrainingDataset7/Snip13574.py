def render_value(key):
            if key in context:
                val = context[key]
            else:
                val = default_value % key if "%s" in default_value else default_value
            return render_value_in_context(val, context)