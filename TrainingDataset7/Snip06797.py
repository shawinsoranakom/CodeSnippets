def as_oracle(self, compiler, connection, **extra_context):
        source_expressions = self.get_source_expressions()
        version = source_expressions[0]
        clone = self.copy()
        clone.set_source_expressions([source_expressions[1]])
        extra_context["function"] = (
            "SDO_UTIL.TO_GML311GEOMETRY"
            if version.value == 3
            else "SDO_UTIL.TO_GMLGEOMETRY"
        )
        return super(AsGML, clone).as_sql(compiler, connection, **extra_context)