def __init__(
        self,
        verbose_name=None,
        name=None,
        encoder=None,
        decoder=None,
        **kwargs,
    ):
        if encoder and not callable(encoder):
            raise ValueError("The encoder parameter must be a callable object.")
        if decoder and not callable(decoder):
            raise ValueError("The decoder parameter must be a callable object.")
        self.encoder = encoder
        self.decoder = decoder
        super().__init__(verbose_name, name, **kwargs)