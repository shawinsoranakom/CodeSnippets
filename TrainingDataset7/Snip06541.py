def __getattr__(self, name):
        m = re.match(r"has_(\w*)_function$", name)
        if m:
            func_name = m[1]
            if func_name not in BaseSpatialOperations.unsupported_functions:
                raise ValueError(
                    f"DatabaseFeatures.has_{func_name}_function isn't valid. "
                    f'Is "{func_name}" missing from '
                    "BaseSpatialOperations.unsupported_functions?"
                )
            return func_name not in self.connection.ops.unsupported_functions
        raise AttributeError