def handler(signal, sender, **kwargs):
            if kwargs["action"] in ["pre_add", "pre_remove"]:
                pk_sets_sent.append(kwargs["pk_set"])