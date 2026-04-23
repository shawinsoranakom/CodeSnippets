def as_oracle(self, compiler, connection, **extra_context):
        lhs, params = compiler.compile(self.lhs)
        sql = (
            "(SELECT DECODE("
            f"SDO_GEOMETRY.GET_GTYPE({lhs}),"
            "1, 'POINT',"
            "2, 'LINESTRING',"
            "3, 'POLYGON',"
            "4, 'COLLECTION',"
            "5, 'MULTIPOINT',"
            "6, 'MULTILINESTRING',"
            "7, 'MULTIPOLYGON',"
            "8, 'SOLID',"
            "'UNKNOWN'))"
        )
        return sql, params