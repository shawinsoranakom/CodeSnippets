def tearDown(self):
        super().tearDown()
        sys.path_hooks.pop(0)