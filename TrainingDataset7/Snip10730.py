def _has_signal_listeners(self, model):
        return signals.pre_delete.has_listeners(
            model
        ) or signals.post_delete.has_listeners(model)