def update(self, parameters: Mapping[str, Any] | ParameterDict) -> None:
        r"""Update the :class:`~torch.nn.ParameterDict` with key-value pairs from ``parameters``, overwriting existing keys.

        .. note::
            If :attr:`parameters` is an ``OrderedDict``, a :class:`~torch.nn.ParameterDict`, or
            an iterable of key-value pairs, the order of new elements in it is preserved.

        Args:
            parameters (iterable): a mapping (dictionary) from string to
                :class:`~torch.nn.Parameter`, or an iterable of
                key-value pairs of type (string, :class:`~torch.nn.Parameter`)
        """
        if not isinstance(parameters, container_abcs.Iterable):
            raise TypeError(
                "ParametersDict.update should be called with an "
                "iterable of key/value pairs, but got " + type(parameters).__name__
            )

        if isinstance(parameters, (OrderedDict, ParameterDict)):
            for key, parameter in parameters.items():
                self[key] = parameter
        elif isinstance(parameters, container_abcs.Mapping):
            for key, parameter in sorted(parameters.items()):
                self[key] = parameter
        else:
            for j, p in enumerate(parameters):
                if not isinstance(p, container_abcs.Iterable):
                    raise TypeError(
                        "ParameterDict update sequence element "
                        "#" + str(j) + " should be Iterable; is" + type(p).__name__
                    )
                # pyrefly: ignore [bad-argument-type]
                if not len(p) == 2:
                    raise ValueError(
                        "ParameterDict update sequence element "
                        # pyrefly: ignore [bad-argument-type]
                        "#" + str(j) + " has length " + str(len(p)) + "; 2 is required"
                    )
                # parameters as length-2 list too cumbersome to type, see ModuleDict.update comment
                self[p[0]] = p[1]