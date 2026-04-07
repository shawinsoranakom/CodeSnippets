def wrapper(*args, **kwargs):
            warnings.warn(
                "`%s.%s` is deprecated, use `%s` instead."
                % (self.class_name, self.old_method_name, self.new_method_name),
                self.deprecation_warning,
                2,
            )
            return f(*args, **kwargs)