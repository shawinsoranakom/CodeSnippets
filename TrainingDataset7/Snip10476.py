def serialize(self):
        return "settings.%s" % self.value.setting_name, {
            "from django.conf import settings"
        }