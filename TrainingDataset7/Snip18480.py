def wrap_with_comment(execute, sql, params, many, context):
            return execute(f"/* My comment */ {sql}", params, many, context)