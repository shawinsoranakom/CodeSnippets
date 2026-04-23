def default(self, o: t.Any) -> t.Any:
        o_type = type(o)

        if o_type is _WrappedValue:  # pylint: disable=unidiomatic-typecheck
            o = o.wrapped
            o_type = type(o)

        if mapped_callable := self._profile.serialize_map.get(o_type):
            return self._profile.maybe_wrap(mapped_callable(o))

        # This is our last chance to intercept the values in containers, so they must be wrapped here.
        # Only containers natively understood by the built-in JSONEncoder are recognized, since any other container types must be present in serialize_map.

        if o_type is dict:  # pylint: disable=unidiomatic-typecheck
            return {self._profile.handle_key(k): self._profile.maybe_wrap(v) for k, v in o.items()}

        if o_type is list or o_type is tuple:  # pylint: disable=unidiomatic-typecheck
            return [self._profile.maybe_wrap(v) for v in o]  # JSONEncoder converts tuple to a list, so just make it a list now

        # Any value here is a type not explicitly handled by this encoder.
        # The profile default handler is responsible for generating an error or converting the value to a supported type.

        return self._profile.default(o)