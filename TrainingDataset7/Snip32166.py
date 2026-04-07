def post_save_handler(signal, sender, instance, **kwargs):
            data.append(
                (instance, sender, kwargs.get("created"), kwargs.get("raw", False))
            )