def setUpClass(cls):
        super().setUpClass()
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        cls.addClassCleanup(shutil.rmtree, MEDIA_ROOT)