def assertDetails(
            details,
            cols,
            primary_key=False,
            unique=False,
            index=False,
            check=False,
            foreign_key=None,
        ):
            # Different backends have different values for same constraints:
            #              PRIMARY KEY     UNIQUE CONSTRAINT    UNIQUE INDEX
            # MySQL     pk=1 uniq=1 idx=1  pk=0 uniq=1 idx=1  pk=0 uniq=1 idx=1
            # Postgres  pk=1 uniq=1 idx=0  pk=0 uniq=1 idx=0  pk=0 uniq=1 idx=1
            # SQLite    pk=1 uniq=0 idx=0  pk=0 uniq=1 idx=0  pk=0 uniq=1 idx=1
            if details["primary_key"]:
                details["unique"] = True
            if details["unique"]:
                details["index"] = False
            self.assertEqual(details["columns"], cols)
            self.assertEqual(details["primary_key"], primary_key)
            self.assertEqual(details["unique"], unique)
            self.assertEqual(details["index"], index)
            self.assertEqual(details["check"], check)
            self.assertEqual(details["foreign_key"], foreign_key)