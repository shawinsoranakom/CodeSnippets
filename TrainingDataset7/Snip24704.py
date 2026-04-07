def as_sql_wrapper(original_as_sql):
            def inner(*args, **kwargs):
                func = original_as_sql.__self__
                # Resolve output_field before as_sql() so touching it in
                # as_sql() won't change __dict__.
                func.output_field
                __dict__original = copy.deepcopy(func.__dict__)
                result = original_as_sql(*args, **kwargs)
                msg = (
                    "%s Func was mutated during compilation." % func.__class__.__name__
                )
                self.assertEqual(func.__dict__, __dict__original, msg)
                return result

            return inner