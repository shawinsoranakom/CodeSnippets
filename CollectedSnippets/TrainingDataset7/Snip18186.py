def setUpClass(cls):
        cls.enterClassContext(
            modify_settings(
                AUTHENTICATION_BACKENDS={"append": cls.backend},
                MIDDLEWARE={"append": cls.middleware},
            )
        )
        super().setUpClass()