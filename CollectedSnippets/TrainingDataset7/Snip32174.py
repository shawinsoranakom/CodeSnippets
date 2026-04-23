def pre_save_handler(signal, sender, instance, **kwargs):
            data.append("pre_save signal, %s" % instance)
            if kwargs.get("raw"):
                data.append("Is raw")