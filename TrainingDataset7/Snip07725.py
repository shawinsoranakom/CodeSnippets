def process_lhs(self, compiler, connection):
        lhs, lhs_params = super().process_lhs(compiler, connection)
        if isinstance(self.lhs.output_field, models.FloatField):
            lhs = "%s::numeric" % lhs
        elif isinstance(self.lhs.output_field, models.SmallIntegerField):
            lhs = "%s::integer" % lhs
        return lhs, lhs_params