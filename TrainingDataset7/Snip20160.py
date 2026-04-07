def test_custom_implementation_year_exact(self):
        try:
            # Two ways to add a customized implementation for different
            # backends:
            # First is MonkeyPatch of the class.
            def as_custom_sql(self, compiler, connection):
                lhs_sql, lhs_params = self.process_lhs(
                    compiler, connection, self.lhs.lhs
                )
                rhs_sql, rhs_params = self.process_rhs(compiler, connection)
                params = lhs_params + rhs_params + lhs_params + rhs_params
                return (
                    "%(lhs)s >= "
                    "str_to_date(concat(%(rhs)s, '-01-01'), '%%%%Y-%%%%m-%%%%d') "
                    "AND %(lhs)s <= "
                    "str_to_date(concat(%(rhs)s, '-12-31'), '%%%%Y-%%%%m-%%%%d')"
                    % {"lhs": lhs_sql, "rhs": rhs_sql},
                    params,
                )

            setattr(YearExact, "as_" + connection.vendor, as_custom_sql)
            self.assertIn(
                "concat(", str(Author.objects.filter(birthdate__testyear=2012).query)
            )
        finally:
            delattr(YearExact, "as_" + connection.vendor)
        try:
            # The other way is to subclass the original lookup and register the
            # subclassed lookup instead of the original.
            class CustomYearExact(YearExact):
                # This method should be named "as_mysql" for MySQL,
                # "as_postgresql" for postgres and so on, but as we don't know
                # which DB we are running on, we need to use setattr.
                def as_custom_sql(self, compiler, connection):
                    lhs_sql, lhs_params = self.process_lhs(
                        compiler, connection, self.lhs.lhs
                    )
                    rhs_sql, rhs_params = self.process_rhs(compiler, connection)
                    params = lhs_params + rhs_params + lhs_params + rhs_params
                    return (
                        "%(lhs)s >= "
                        "str_to_date(CONCAT(%(rhs)s, '-01-01'), '%%%%Y-%%%%m-%%%%d') "
                        "AND %(lhs)s <= "
                        "str_to_date(CONCAT(%(rhs)s, '-12-31'), '%%%%Y-%%%%m-%%%%d')"
                        % {"lhs": lhs_sql, "rhs": rhs_sql},
                        params,
                    )

            setattr(
                CustomYearExact,
                "as_" + connection.vendor,
                CustomYearExact.as_custom_sql,
            )
            YearTransform.register_lookup(CustomYearExact)
            self.assertIn(
                "CONCAT(", str(Author.objects.filter(birthdate__testyear=2012).query)
            )
        finally:
            YearTransform._unregister_lookup(CustomYearExact)
            YearTransform.register_lookup(YearExact)