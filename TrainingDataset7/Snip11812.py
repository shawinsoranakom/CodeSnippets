def split_parameter_list_as_sql(self, compiler, connection):
        # This is a special case for databases which limit the number of
        # elements which can appear in an 'IN' clause.
        max_in_list_size = connection.ops.max_in_list_size()
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.batch_process_rhs(compiler, connection)
        in_clause_elements = ["("]
        params = []
        for offset in range(0, len(rhs_params), max_in_list_size):
            if offset > 0:
                in_clause_elements.append(" OR ")
            in_clause_elements.append("%s IN (" % lhs)
            params.extend(lhs_params)
            sqls = rhs[offset : offset + max_in_list_size]
            sqls_params = rhs_params[offset : offset + max_in_list_size]
            param_group = ", ".join(sqls)
            in_clause_elements.append(param_group)
            in_clause_elements.append(")")
            params.extend(sqls_params)
        in_clause_elements.append(")")
        return "".join(in_clause_elements), params