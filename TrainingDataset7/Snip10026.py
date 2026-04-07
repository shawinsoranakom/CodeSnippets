def combine_duration_expression(self, connector, sub_expressions):
        if connector not in ["+", "-", "*", "/"]:
            raise DatabaseError("Invalid connector for timedelta: %s." % connector)
        fn_params = ["'%s'" % connector, *sub_expressions]
        if len(fn_params) > 3:
            raise ValueError("Too many params for timedelta operations.")
        return "django_format_dtdelta(%s)" % ", ".join(fn_params)