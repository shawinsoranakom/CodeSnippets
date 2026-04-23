def spatial_function_name(self, func_name):
        if func_name in self.unsupported_functions:
            raise NotSupportedError(
                "This backend doesn't support the %s function." % func_name
            )
        return self.function_names.get(func_name, self.geom_func_prefix + func_name)