def tearDown(self):
        if self.old_DJANGO_AUTO_COMPLETE:
            os.environ["DJANGO_AUTO_COMPLETE"] = self.old_DJANGO_AUTO_COMPLETE
        else:
            del os.environ["DJANGO_AUTO_COMPLETE"]