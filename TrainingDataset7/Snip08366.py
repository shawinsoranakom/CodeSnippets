def app_model_error(model_key):
        try:
            apps.get_app_config(model_key[0])
            model_error = "app '%s' doesn't provide model '%s'" % model_key
        except LookupError:
            model_error = "app '%s' isn't installed" % model_key[0]
        return model_error