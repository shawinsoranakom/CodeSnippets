def setUpClass(cls):
        cls.enterClassContext(
            modify_settings(AUTHENTICATION_BACKENDS={"append": cls.backend})
        )
        super().setUpClass()