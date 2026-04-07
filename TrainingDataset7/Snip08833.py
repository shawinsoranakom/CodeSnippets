def model_installed(model):
            opts = model._meta
            converter = connection.introspection.identifier_converter
            max_name_length = connection.ops.max_name_length()
            return not (
                (converter(truncate_name(opts.db_table, max_name_length)) in tables)
                or (
                    opts.auto_created
                    and converter(opts.auto_created._meta.db_table) in tables
                )
            )