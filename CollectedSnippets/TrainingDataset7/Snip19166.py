def test_createcachetable_observes_database_router(self):
        # cache table should not be created on 'default'
        with self.assertNumQueries(0, using="default"):
            management.call_command("createcachetable", database="default", verbosity=0)
        # cache table should be created on 'other'
        # Queries:
        #   1: check table doesn't already exist
        #   2: create savepoint (if transactional DDL is supported)
        #   3: create the table
        #   4: create the index
        #   5: release savepoint (if transactional DDL is supported)
        num = 5 if connections["other"].features.can_rollback_ddl else 3
        with self.assertNumQueries(num, using="other"):
            management.call_command("createcachetable", database="other", verbosity=0)