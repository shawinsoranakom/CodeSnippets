def _initialize_signal_person(self):
        # Install a listener on the two m2m relations.
        models.signals.m2m_changed.connect(
            self.m2m_changed_signal_receiver, Person.fans.through
        )
        models.signals.m2m_changed.connect(
            self.m2m_changed_signal_receiver, Person.friends.through
        )