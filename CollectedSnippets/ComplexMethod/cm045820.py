def __init__(
        self,
        backbone_config=None,
        class_thresholds: Optional[List[float]] = None,
        class_order: Optional[List[int]] = None,
        reading_order_config: Optional[Union[PPDocLayoutV2ReadingOrderConfig, Dict]] = None,
        **kwargs,
    ):
        if backbone_config is None:
            backbone_config = _build_default_backbone_config()
        if isinstance(reading_order_config, PPDocLayoutV2ReadingOrderConfig):
            reading_order = reading_order_config
        else:
            reading_order = PPDocLayoutV2ReadingOrderConfig(**(reading_order_config or {}))

        super().__init__(
            backbone_config=backbone_config,
            class_thresholds=class_thresholds or list(DEFAULT_CLASS_THRESHOLDS),
            class_order=class_order or list(DEFAULT_CLASS_ORDER),
            **kwargs,
        )
        self.class_thresholds = list(class_thresholds or DEFAULT_CLASS_THRESHOLDS)
        self.class_order = list(class_order or DEFAULT_CLASS_ORDER)
        self.reading_order_config = reading_order