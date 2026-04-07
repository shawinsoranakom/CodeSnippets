def test_lazy(self):
        storage_base_import_path = "django.contrib.messages.storage.base"
        in_use_base = sys.modules.pop(storage_base_import_path)
        self.addCleanup(sys.modules.__setitem__, storage_base_import_path, in_use_base)
        # Don't use @override_settings to avoid calling the setting_changed
        # signal, but ensure that base.LEVEL_TAGS hasn't been read yet (this
        # means that we need to ensure the `base` module is freshly imported).
        base = importlib.import_module(storage_base_import_path)
        old_message_tags = getattr(settings, "MESSAGE_TAGS", None)
        settings.MESSAGE_TAGS = {constants.ERROR: "bad"}
        try:
            self.assertEqual(base.LEVEL_TAGS[constants.ERROR], "bad")
        finally:
            if old_message_tags is None:
                del settings.MESSAGE_TAGS
            else:
                settings.MESSAGE_TAGS = old_message_tags