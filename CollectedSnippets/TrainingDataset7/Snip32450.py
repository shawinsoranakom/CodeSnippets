def test_dir_not_exists(self, **kwargs):
        shutil.rmtree(settings.STATIC_ROOT)
        super().run_collectstatic(clear=True)