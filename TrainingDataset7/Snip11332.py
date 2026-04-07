def _as_sql_parts(self, compiler, connection):
        # Process JSON path from the left-hand side.
        if isinstance(self.lhs, KeyTransform):
            lhs_sql, lhs_params, lhs_key_transforms = self.lhs.preprocess_lhs(
                compiler, connection
            )
            lhs_json_path = connection.ops.compile_json_path(lhs_key_transforms)
        else:
            lhs_sql, lhs_params = self.process_lhs(compiler, connection)
            lhs_json_path = "$"
        # Process JSON path from the right-hand side.
        rhs = self.rhs
        if not isinstance(rhs, (list, tuple)):
            rhs = [rhs]
        for key in rhs:
            if isinstance(key, KeyTransform):
                *_, rhs_key_transforms = key.preprocess_lhs(compiler, connection)
            else:
                rhs_key_transforms = [key]
            *rhs_key_transforms, final_key = rhs_key_transforms
            rhs_json_path = connection.ops.compile_json_path(
                rhs_key_transforms, include_root=False
            )
            rhs_json_path += self.compile_json_path_final_key(connection, final_key)
            yield lhs_sql, lhs_params, lhs_json_path + rhs_json_path