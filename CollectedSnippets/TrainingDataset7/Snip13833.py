def user_model_swapped(*, setting, **kwargs):
    if setting == "AUTH_USER_MODEL":
        apps.clear_cache()
        try:
            from django.contrib.auth import get_user_model

            UserModel = get_user_model()
        except ImproperlyConfigured:
            # Some tests set an invalid AUTH_USER_MODEL.
            pass
        else:
            from django.contrib.auth import backends

            backends.UserModel = UserModel

            from django.contrib.auth import forms

            forms.UserModel = UserModel

            from django.contrib.auth.handlers import modwsgi

            modwsgi.UserModel = UserModel

            from django.contrib.auth.management.commands import changepassword

            changepassword.UserModel = UserModel

            from django.contrib.auth import views

            views.UserModel = UserModel