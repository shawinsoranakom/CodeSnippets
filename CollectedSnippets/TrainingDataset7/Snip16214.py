def tearDown(self):
        # Reset the routers' state between each test.
        Router.target_db = None