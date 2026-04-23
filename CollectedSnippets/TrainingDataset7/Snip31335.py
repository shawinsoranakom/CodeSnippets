def _add_ci_collation(self):
        ci_collation = "case_insensitive"

        def drop_collation():
            with connection.cursor() as cursor:
                cursor.execute(f"DROP COLLATION IF EXISTS {ci_collation}")

        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE COLLATION IF NOT EXISTS {ci_collation} (provider=icu, "
                f"locale='und-u-ks-level2', deterministic=false)"
            )
        self.addCleanup(drop_collation)
        return ci_collation