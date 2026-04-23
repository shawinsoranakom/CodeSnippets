def regex_lookup(self, lookup_type):
        # REGEXP_LIKE doesn't exist in MariaDB.
        if self.connection.mysql_is_mariadb:
            if lookup_type == "regex":
                return "%s REGEXP BINARY %s"
            return "%s REGEXP %s"

        match_option = "c" if lookup_type == "regex" else "i"
        return "REGEXP_LIKE(%%s, %%s, '%s')" % match_option