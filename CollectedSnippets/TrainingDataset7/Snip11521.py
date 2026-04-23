def __set__(self, instance, value):
        raise TypeError(
            "Direct assignment to the %s is prohibited. Use %s.set() instead."
            % self._get_set_deprecation_msg_params(),
        )