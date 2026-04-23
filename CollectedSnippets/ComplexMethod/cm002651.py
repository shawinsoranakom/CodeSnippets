def __call__(self, *args, **kwargs):
        if self.gradient_checkpointing and self.training:
            do_warn = False
            layer_name = self.__class__.__name__
            message = f"Caching is incompatible with gradient checkpointing in {layer_name}. Setting"

            if "use_cache" in kwargs and kwargs["use_cache"]:
                kwargs["use_cache"] = False
                message += " `use_cache=False`,"
                do_warn = True

            # different names for the same thing in different layers
            # TODO cyril: this one without `S` can be removed after deprecation cycle
            if "past_key_value" in kwargs and kwargs["past_key_value"] is not None:
                kwargs["past_key_value"] = None
                message += " `past_key_value=None`,"
                do_warn = True

            if "past_key_values" in kwargs and kwargs["past_key_values"] is not None:
                kwargs["past_key_values"] = None
                message += " `past_key_values=None`,"
                do_warn = True

            if "layer_past" in kwargs and kwargs["layer_past"] is not None:
                kwargs["layer_past"] = None
                message += " `layer_past=None`,"
                do_warn = True

            # warn if anything was changed
            if do_warn:
                message = message.rstrip(",") + "."
                logger.warning_once(message)

            return self._gradient_checkpointing_func(partial(super().__call__, **kwargs), *args)
        return super().__call__(*args, **kwargs)