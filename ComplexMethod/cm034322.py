def getattr(self, obj: t.Any, attribute: str) -> t.Any:
        """
        Get `attribute` from the attributes of `obj`, falling back to items in `obj`.
        If no item was found, return a sandbox-specific `UndefinedMarker` if `attribute` is protected by the sandbox,
        otherwise return a normal `UndefinedMarker` instance.
        This differs from the built-in Jinja behavior which will not fall back to items if `attribute` is protected by the sandbox.
        """
        # example template that uses this: "{{ some.thing }}" -- obj is the "some" dict, attribute is "thing"

        is_safe = True

        try:
            value = getattr(obj, attribute)
        except _attribute_unavailable.AttributeUnavailableError as ex:
            value = self.undefined(obj=obj, name=attribute, hint=_error_utils.format_exception_message(ex))
        except AttributeError:
            value = _sentinel
        else:
            if not (is_safe := self.is_safe_attribute(obj, attribute, value)):
                value = _sentinel

        if value is _sentinel:
            try:
                value = obj[attribute]
            except (TypeError, LookupError):
                value = self.undefined(obj=obj, name=attribute) if is_safe else self.unsafe_undefined(obj, attribute)

        AnsibleAccessContext.current().access(value)

        return value