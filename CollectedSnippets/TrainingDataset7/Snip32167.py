def pre_delete_handler(signal, sender, instance, origin, **kwargs):
            data.append((instance, sender, instance.id is None, origin))