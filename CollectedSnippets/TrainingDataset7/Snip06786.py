def resolve_expression(self, *args, **kwargs):
        res = super().resolve_expression(*args, **kwargs)
        if not self.geom_param_pos:
            return res

        # Ensure that expressions are geometric.
        source_fields = res.get_source_fields()
        for pos in self.geom_param_pos:
            field = source_fields[pos]
            if not isinstance(field, GeometryField):
                raise TypeError(
                    "%s function requires a GeometryField in position %s, got %s."
                    % (
                        self.name,
                        pos + 1,
                        type(field).__name__,
                    )
                )

        base_srid = res.geo_field.srid
        for pos in self.geom_param_pos[1:]:
            expr = res.source_expressions[pos]
            expr_srid = expr.output_field.srid
            if expr_srid != base_srid:
                # Automatic SRID conversion so objects are comparable.
                res.source_expressions[pos] = Transform(
                    expr, base_srid
                ).resolve_expression(*args, **kwargs)
        return res