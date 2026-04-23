def _resolve_lookup(self, context):
        """
        Perform resolution of a real variable (i.e. not a literal) against the
        given context.

        As indicated by the method's name, this method is an implementation
        detail and shouldn't be called by external code. Use Variable.resolve()
        instead.
        """
        current = context
        try:  # catch-all for silent variable failures
            for bit in self.lookups:
                try:  # dictionary lookup
                    # Only allow if the metaclass implements __getitem__. See
                    # https://docs.python.org/3/reference/datamodel.html#classgetitem-versus-getitem
                    if not hasattr(type(current), "__getitem__"):
                        raise TypeError
                    current = current[bit]
                    # ValueError/IndexError are for numpy.array lookup on
                    # numpy < 1.9 and 1.9+ respectively
                except (TypeError, AttributeError, KeyError, ValueError, IndexError):
                    try:  # attribute lookup
                        # Don't return class attributes if the class is the
                        # context:
                        if isinstance(current, BaseContext) and getattr(
                            type(current), bit
                        ):
                            raise AttributeError
                        current = getattr(current, bit)
                    except (TypeError, AttributeError):
                        # Reraise if the exception was raised by a @property
                        if not isinstance(current, BaseContext) and bit in dir(current):
                            raise
                        try:  # list-index lookup
                            current = current[int(bit)]
                        except (
                            IndexError,  # list index out of range
                            ValueError,  # invalid literal for int()
                            KeyError,  # current is a dict without `int(bit)` key
                            TypeError,
                        ):  # unsubscriptable object
                            raise VariableDoesNotExist(
                                "Failed lookup for key [%s] in %r",
                                (bit, current),
                            )  # missing attribute
                if callable(current):
                    if getattr(current, "do_not_call_in_templates", False):
                        pass
                    elif getattr(current, "alters_data", False):
                        current = context.template.engine.string_if_invalid
                    else:
                        try:  # method call (assuming no args required)
                            current = current()
                        except TypeError:
                            try:
                                current_signature = signature(current)
                            except ValueError:  # No signature found.
                                current = context.template.engine.string_if_invalid
                            else:
                                try:
                                    current_signature.bind()
                                except TypeError:  # Arguments *were* required.
                                    # Invalid method call.
                                    current = context.template.engine.string_if_invalid
                                else:
                                    raise
        except Exception as e:
            template_name = getattr(context, "template_name", None) or "unknown"
            logger.debug(
                "Exception while resolving variable '%s' in template '%s'.",
                bit,
                template_name,
                exc_info=True,
            )

            if getattr(e, "silent_variable_failure", False):
                current = context.template.engine.string_if_invalid
            else:
                raise

        return current