def setUp(self):
        self.old_DJANGO_AUTO_COMPLETE = os.environ.get("DJANGO_AUTO_COMPLETE")
        os.environ["DJANGO_AUTO_COMPLETE"] = "1"