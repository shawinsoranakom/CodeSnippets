def __getattr__(self, real_name):
        from django.conf import settings

        if settings.USE_I18N:
            from django.utils.translation import trans_real as trans
            from django.utils.translation.reloader import (
                translation_file_changed,
                watch_for_translation_changes,
            )

            autoreload_started.connect(
                watch_for_translation_changes, dispatch_uid="translation_file_changed"
            )
            file_changed.connect(
                translation_file_changed, dispatch_uid="translation_file_changed"
            )
        else:
            from django.utils.translation import trans_null as trans
        setattr(self, real_name, getattr(trans, real_name))
        return getattr(trans, real_name)