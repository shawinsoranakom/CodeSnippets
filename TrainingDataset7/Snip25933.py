def _initialize_signal_car(self, add_default_parts_before_set_signal=False):
        """Install a listener on the two m2m relations."""
        models.signals.m2m_changed.connect(
            self.m2m_changed_signal_receiver, Car.optional_parts.through
        )
        if add_default_parts_before_set_signal:
            # adding a default part to our car - no signal listener installed
            self.vw.default_parts.add(self.sunroof)
        models.signals.m2m_changed.connect(
            self.m2m_changed_signal_receiver, Car.default_parts.through
        )