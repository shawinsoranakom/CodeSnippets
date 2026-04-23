def __enter__(self):
        self.mocker = mock.patch(
            "django.core.management.utils.shutil.which",
            return_value=self.shutil_which_result,
        )
        self.mocker.start()
        return self