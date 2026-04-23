def _get_connector_class_with_compat(
        cls, kv_transfer_config: "KVTransferConfig"
    ) -> tuple[type[KVConnectorBaseType], bool]:
        connector_name = kv_transfer_config.kv_connector
        if connector_name is None:
            raise ValueError("Connector name is not set in KVTransferConfig")
        compat_sig = False
        connector_module_path = kv_transfer_config.kv_connector_module_path
        if connector_module_path is not None and not connector_module_path:
            raise ValueError("kv_connector_module_path cannot be an empty string.")
        if connector_module_path:
            # External module path takes priority over internal registry.
            connector_module = importlib.import_module(connector_module_path)
            try:
                connector_cls = getattr(connector_module, connector_name)
            except AttributeError as e:
                raise AttributeError(
                    f"Class {connector_name} not found in {connector_module_path}"
                ) from e
            connector_cls = cast(type[KVConnectorBaseType], connector_cls)
            if not supports_kw(connector_cls, "kv_cache_config"):
                compat_sig = True
                logger.warning(
                    "Connector %s uses deprecated signature with 2 required arguments. "
                    "Please update to include kv_cache_config as the second argument.",
                    connector_cls.__name__,
                )
        elif connector_name in cls._registry:
            connector_cls = cls._registry[connector_name]()
        else:
            raise ValueError(f"Unsupported connector type: {connector_name}")
        return connector_cls, compat_sig