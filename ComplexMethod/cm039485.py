def __call__(self, estimator, *args, **kwargs):
        """Evaluate predicted target values."""
        scores = {}
        cache = {} if self._use_cache(estimator) else None
        cached_call = partial(_cached_call, cache)

        if _routing_enabled():
            routed_params = process_routing(self, "score", **kwargs)
        else:
            # Scorers all get the same args, and get all of them except sample_weight.
            # Only the ones having `sample_weight` in their signature will receive it.
            # This does not work for metadata other than sample_weight, and for those
            # users have to enable metadata routing.
            common_kwargs = {
                arg: value for arg, value in kwargs.items() if arg != "sample_weight"
            }
            routed_params = Bunch(
                **{name: Bunch(score=common_kwargs.copy()) for name in self._scorers}
            )
            if "sample_weight" in kwargs:
                for name, scorer in self._scorers.items():
                    if scorer._accept_sample_weight():
                        routed_params[name].score["sample_weight"] = kwargs[
                            "sample_weight"
                        ]

        for name, scorer in self._scorers.items():
            try:
                if isinstance(scorer, _BaseScorer):
                    score = scorer._score(
                        cached_call, estimator, *args, **routed_params.get(name).score
                    )
                else:
                    score = scorer(estimator, *args, **routed_params.get(name).score)
                scores[name] = score
            except Exception as e:
                if self._raise_exc:
                    raise e
                else:
                    scores[name] = format_exc()
        return scores