def __init__(
        self,
        mixture_distribution: Categorical,
        component_distribution: Distribution,
        validate_args: bool | None = None,
    ) -> None:
        self._mixture_distribution = mixture_distribution
        self._component_distribution = component_distribution

        if not isinstance(self._mixture_distribution, Categorical):
            raise ValueError(
                " The Mixture distribution needs to be an "
                " instance of torch.distributions.Categorical"
            )

        if not isinstance(self._component_distribution, Distribution):
            raise ValueError(
                "The Component distribution need to be an "
                "instance of torch.distributions.Distribution"
            )

        # Check that batch size matches
        mdbs = self._mixture_distribution.batch_shape
        cdbs = self._component_distribution.batch_shape[:-1]
        for size1, size2 in zip(reversed(mdbs), reversed(cdbs)):
            if size1 != 1 and size2 != 1 and size1 != size2:
                raise ValueError(
                    f"`mixture_distribution.batch_shape` ({mdbs}) is not "
                    "compatible with `component_distribution."
                    f"batch_shape`({cdbs})"
                )

        # Check that the number of mixture component matches
        km = self._mixture_distribution.logits.shape[-1]
        kc = self._component_distribution.batch_shape[-1]
        if km is not None and kc is not None and km != kc:
            raise ValueError(
                f"`mixture_distribution component` ({km}) does not"
                " equal `component_distribution.batch_shape[-1]`"
                f" ({kc})"
            )
        self._num_component = km

        event_shape = self._component_distribution.event_shape
        self._event_ndims = len(event_shape)
        super().__init__(
            # pyrefly: ignore [bad-argument-type]
            batch_shape=cdbs,
            event_shape=event_shape,
            validate_args=validate_args,
        )