def ready(self):
        post_migrate.connect(
            rename_permissions_after_model_rename,
            dispatch_uid="django.contrib.auth.management.rename_permissions",
        )
        post_migrate.connect(
            create_permissions,
            dispatch_uid="django.contrib.auth.management.create_permissions",
        )
        last_login_field = getattr(get_user_model(), "last_login", None)
        # Register the handler only if UserModel.last_login is a field.
        if isinstance(last_login_field, DeferredAttribute):
            from .models import update_last_login

            user_logged_in.connect(update_last_login, dispatch_uid="update_last_login")
        checks.register(check_user_model, checks.Tags.models)
        checks.register(check_models_permissions, checks.Tags.models)
        checks.register(check_middleware)