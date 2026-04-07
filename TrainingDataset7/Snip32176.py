def pre_delete_handler(signal, sender, instance, **kwargs):
            data.append("pre_delete signal, %s" % instance)
            data.append("instance.id is not None: %s" % (instance.id is not None))