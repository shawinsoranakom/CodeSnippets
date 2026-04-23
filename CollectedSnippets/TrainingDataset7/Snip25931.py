def m2m_changed_signal_receiver(self, signal, sender, **kwargs):
        message = {
            "instance": kwargs["instance"],
            "action": kwargs["action"],
            "reverse": kwargs["reverse"],
            "model": kwargs["model"],
            "raw": kwargs["raw"],
        }
        if kwargs["pk_set"]:
            message["objects"] = list(
                kwargs["model"].objects.filter(pk__in=kwargs["pk_set"])
            )
        self.m2m_changed_messages.append(message)