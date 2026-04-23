def tearDown(self):
        # disconnect all signal handlers
        models.signals.m2m_changed.disconnect(
            self.m2m_changed_signal_receiver, Car.default_parts.through
        )
        models.signals.m2m_changed.disconnect(
            self.m2m_changed_signal_receiver, Car.optional_parts.through
        )
        models.signals.m2m_changed.disconnect(
            self.m2m_changed_signal_receiver, Person.fans.through
        )
        models.signals.m2m_changed.disconnect(
            self.m2m_changed_signal_receiver, Person.friends.through
        )