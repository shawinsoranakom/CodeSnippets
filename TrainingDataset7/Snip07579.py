def ready(self):
        setting_changed.connect(update_level_tags)