def test_invalid_path(self):
        obj = DeconstructibleInvalidPathClass()
        docs_version = get_docs_version()
        msg = (
            f"Could not find object DeconstructibleInvalidPathClass in "
            f"utils_tests.deconstructible_classes.\n"
            f"Please note that you cannot serialize things like inner "
            f"classes. Please move the object into the main module body to "
            f"use migrations.\n"
            f"For more information, see "
            f"https://docs.djangoproject.com/en/{docs_version}/topics/"
            f"migrations/#serializing-values"
        )
        with self.assertRaisesMessage(ValueError, msg):
            obj.deconstruct()