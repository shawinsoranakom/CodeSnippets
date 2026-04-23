def test_database_routing(self):
        class WriteToOtherRouter:
            def db_for_write(self, model, **hints):
                return "other"

        with self.settings(DATABASE_ROUTERS=[WriteToOtherRouter()]):
            with (
                self.assertNumQueries(0, using="default"),
                self.assertNumQueries(
                    1,
                    using="other",
                ),
            ):
                self.q1.set_answer_order([3, 1, 2, 4])