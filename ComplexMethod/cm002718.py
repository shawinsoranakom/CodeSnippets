def __post_init__(self):
        if self.log_history is None:
            self.log_history = []
        if self.stateful_callbacks is None:
            self.stateful_callbacks = {}
        elif isinstance(self.stateful_callbacks, dict):
            # We are loading the callbacks in from the state file, no need to process them
            pass
        else:
            # Saveable callbacks get stored as dict of kwargs
            stateful_callbacks = {}
            for callback in self.stateful_callbacks:
                if not isinstance(callback, (ExportableState)):
                    raise TypeError(
                        f"All callbacks passed to be saved must inherit `ExportableState`, but received {type(callback)}"
                    )
                name = callback.__class__.__name__
                if name in stateful_callbacks:
                    # We can have multiple versions of the same callback
                    # if so, we store them as a list of states to restore
                    if not isinstance(stateful_callbacks[name], list):
                        stateful_callbacks[name] = [stateful_callbacks[name]]
                    stateful_callbacks[name].append(callback.state())
                else:
                    stateful_callbacks[name] = callback.state()
            self.stateful_callbacks = stateful_callbacks