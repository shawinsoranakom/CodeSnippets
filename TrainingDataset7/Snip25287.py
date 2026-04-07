def test_get_constraints(self):
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

        # Test custom constraints
        custom_constraints = {
            "article_email_pub_date_uniq",
            "email_pub_date_idx",
        }
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, Comment._meta.db_table
            )
            if (
                connection.features.supports_column_check_constraints
                and connection.features.can_introspect_check_constraints
            ):
                constraints.update(
                    connection.introspection.get_constraints(
                        cursor, CheckConstraintModel._meta.db_table
                    )
                )
                custom_constraints.add("up_votes_gte_0_check")
                assertDetails(
                    constraints["up_votes_gte_0_check"], ["up_votes"], check=True
                )
        assertDetails(
            constraints["article_email_pub_date_uniq"],
            ["article_id", "email", "pub_date"],
            unique=True,
        )
        assertDetails(
            constraints["email_pub_date_idx"], ["email", "pub_date"], index=True
        )
        # Test field constraints
        field_constraints = set()
        for name, details in constraints.items():
            if name in custom_constraints:
                continue
            elif details["columns"] == ["up_votes"] and details["check"]:
                assertDetails(details, ["up_votes"], check=True)
                field_constraints.add(name)
            elif details["columns"] == ["voting_number"] and details["check"]:
                assertDetails(details, ["voting_number"], check=True)
                field_constraints.add(name)
            elif details["columns"] == ["ref"] and details["unique"]:
                assertDetails(details, ["ref"], unique=True)
                field_constraints.add(name)
            elif details["columns"] == ["voting_number"] and details["unique"]:
                assertDetails(details, ["voting_number"], unique=True)
                field_constraints.add(name)
            elif details["columns"] == ["article_id"] and details["index"]:
                assertDetails(details, ["article_id"], index=True)
                field_constraints.add(name)
            elif details["columns"] == ["id"] and details["primary_key"]:
                assertDetails(details, ["id"], primary_key=True, unique=True)
                field_constraints.add(name)
            elif details["columns"] == ["article_id"] and details["foreign_key"]:
                assertDetails(
                    details, ["article_id"], foreign_key=("introspection_article", "id")
                )
                field_constraints.add(name)
            elif details["check"]:
                # Some databases (e.g. Oracle) include additional check
                # constraints.
                field_constraints.add(name)
        # All constraints are accounted for.
        self.assertEqual(
            constraints.keys() ^ (custom_constraints | field_constraints), set()
        )