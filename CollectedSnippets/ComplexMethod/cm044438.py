def __init__(self,
                 filters: int,
                 kernel_size: int | tuple[int, int] = 5,
                 strides: int | tuple[int, int] = 2,
                 padding: str = "same",
                 normalization: str | None = None,
                 activation: str | None = "leakyrelu",
                 use_depthwise: bool = False,
                 relu_alpha: float = 0.1,
                 **kwargs) -> None:
        logger.debug(parse_class_init(locals()))

        self._name = kwargs.pop("name") if "name" in kwargs else _get_name(f"conv_{filters}")
        self._use_reflect_padding = cfg.reflect_padding()

        kernel_size = (kernel_size, kernel_size) if isinstance(kernel_size, int) else kernel_size
        self._args = (kernel_size, ) if use_depthwise else (filters, kernel_size)
        self._strides = (strides, strides) if isinstance(strides, int) else strides
        self._padding = "valid" if self._use_reflect_padding else padding
        self._kwargs = kwargs
        self._normalization = None if not normalization else normalization.lower()
        self._activation = None if not activation else activation.lower()
        self._use_depthwise = use_depthwise
        self._relu_alpha = relu_alpha

        self._assert_arguments()
        self._layers = self._get_layers()
        logger.debug("Initialized %s", self.__class__.__name__)