def test_router_init_default(self):
        connection_router = ConnectionRouter()
        self.assertEqual(
            [r.__class__.__name__ for r in connection_router.routers],
            ["TestRouter", "WriteRouter"],
        )