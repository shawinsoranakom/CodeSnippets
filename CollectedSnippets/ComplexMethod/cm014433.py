def __call__(self, cls):
        if issubclass(cls, IterDataPipe):
            if isinstance(cls, type):  # type: ignore[arg-type]
                if not isinstance(cls, _DataPipeMeta):
                    raise TypeError(
                        "`functional_datapipe` can only decorate IterDataPipe"
                    )
            # with non_deterministic decorator
            else:
                if not isinstance(cls, non_deterministic) and not (
                    hasattr(cls, "__self__")
                    and isinstance(cls.__self__, non_deterministic)
                ):
                    raise TypeError(
                        "`functional_datapipe` can only decorate IterDataPipe"
                    )
            IterDataPipe.register_datapipe_as_function(
                self.name, cls, enable_df_api_tracing=self.enable_df_api_tracing
            )
        elif issubclass(cls, MapDataPipe):
            MapDataPipe.register_datapipe_as_function(self.name, cls)

        return cls