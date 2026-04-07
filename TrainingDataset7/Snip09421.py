def _check_sql(self, name, check):
        return self.sql_constraint % {
            "name": self.quote_name(name),
            "constraint": self.sql_check_constraint % {"check": check},
        }