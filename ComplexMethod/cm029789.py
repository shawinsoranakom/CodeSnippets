def _check_callback(self):
        if self.action == "callback":
            if not callable(self.callback):
                raise OptionError(
                    "callback not callable: %r" % self.callback, self)
            if (self.callback_args is not None and
                not isinstance(self.callback_args, tuple)):
                raise OptionError(
                    "callback_args, if supplied, must be a tuple: not %r"
                    % self.callback_args, self)
            if (self.callback_kwargs is not None and
                not isinstance(self.callback_kwargs, dict)):
                raise OptionError(
                    "callback_kwargs, if supplied, must be a dict: not %r"
                    % self.callback_kwargs, self)
        else:
            if self.callback is not None:
                raise OptionError(
                    "callback supplied (%r) for non-callback option"
                    % self.callback, self)
            if self.callback_args is not None:
                raise OptionError(
                    "callback_args supplied for non-callback option", self)
            if self.callback_kwargs is not None:
                raise OptionError(
                    "callback_kwargs supplied for non-callback option", self)