def pre_save_handler(signal, sender, instance, **kwargs):
            data.append((instance, sender, kwargs.get("raw", False)))