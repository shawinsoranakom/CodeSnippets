def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(
            modify_settings(ALLOWED_HOSTS={"append": cls.allowed_host})
        )
        cls._start_server_thread()