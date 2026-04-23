def test_router_init_arg(self):
        connection_router = ConnectionRouter(
            [
                "multiple_database.tests.TestRouter",
                "multiple_database.tests.WriteRouter",
            ]
        )
        self.assertEqual(
            [r.__class__.__name__ for r in connection_router.routers],
            ["TestRouter", "WriteRouter"],
        )

        # Init with instances instead of strings
        connection_router = ConnectionRouter([TestRouter(), WriteRouter()])
        self.assertEqual(
            [r.__class__.__name__ for r in connection_router.routers],
            ["TestRouter", "WriteRouter"],
        )