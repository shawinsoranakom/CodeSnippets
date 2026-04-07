def setUpClass(cls):
        # nl/formats.py has customized TIME_INPUT_FORMATS:
        # ['%H:%M:%S', '%H.%M:%S', '%H.%M', '%H:%M']
        cls.enterClassContext(translation.override("nl"))
        super().setUpClass()