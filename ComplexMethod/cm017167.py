def connect(self, receiver, sender=None, weak=True, dispatch_uid=None):
        """
        Connect receiver to sender for signal.

        Arguments:

            receiver
                A function or an instance method which is to receive signals.
                Receivers must be hashable objects. Receivers can be
                asynchronous.

                If weak is True, then receiver must be weak referenceable.

                Receivers must be able to accept keyword arguments.

                If a receiver is connected with a dispatch_uid argument, it
                will not be added if another receiver was already connected
                with that dispatch_uid.

            sender
                The sender to which the receiver should respond. Must either be
                a Python object, or None to receive events from any sender.

            weak
                Whether to use weak references to the receiver. By default, the
                module will attempt to use weak references to the receiver
                objects. If this parameter is false, then strong references
                will be used.

            dispatch_uid
                An identifier used to uniquely identify a particular instance
                of a receiver. This will usually be a string, though it may be
                anything hashable.
        """
        from django.conf import settings

        # If DEBUG is on, check that we got a good receiver
        if settings.configured and settings.DEBUG:
            if not callable(receiver):
                raise TypeError("Signal receivers must be callable.")
            # Check for **kwargs
            if not func_accepts_kwargs(receiver):
                raise ValueError(
                    "Signal receivers must accept keyword arguments (**kwargs)."
                )

        if dispatch_uid:
            lookup_key = (dispatch_uid, _make_id(sender))
        else:
            lookup_key = (_make_id(receiver), _make_id(sender))

        is_async = iscoroutinefunction(receiver)

        if weak:
            ref = weakref.ref
            # Check for bound methods
            if hasattr(receiver, "__self__") and hasattr(receiver, "__func__"):
                ref = weakref.WeakMethod
            receiver = ref(receiver, self._flag_dead_receivers)

        # Keep a weakref to sender if possible to ensure associated receivers
        # are cleared if it gets garbage collected. This ensures there is no
        # id(sender) collisions for distinct senders with non-overlapping
        # lifetimes.
        sender_ref = None
        if sender is not None:
            try:
                sender_ref = weakref.ref(sender, self._flag_dead_receivers)
            except TypeError:
                pass

        with self.lock:
            self._clear_dead_receivers()
            if not any(r_key == lookup_key for r_key, _, _, _ in self.receivers):
                self.receivers.append((lookup_key, receiver, sender_ref, is_async))
            self.sender_receivers_cache.clear()