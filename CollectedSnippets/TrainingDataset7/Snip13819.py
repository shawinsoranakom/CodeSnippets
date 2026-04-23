def update_installed_apps(*, setting, **kwargs):
    if setting == "INSTALLED_APPS":
        # Rebuild any AppDirectoriesFinder instance.
        from django.contrib.staticfiles.finders import get_finder

        get_finder.cache_clear()
        # Rebuild management commands cache
        from django.core.management import get_commands

        get_commands.cache_clear()
        # Rebuild get_app_template_dirs cache.
        from django.template.utils import get_app_template_dirs

        get_app_template_dirs.cache_clear()
        # Rebuild translations cache.
        from django.utils.translation import trans_real

        trans_real._translations = {}