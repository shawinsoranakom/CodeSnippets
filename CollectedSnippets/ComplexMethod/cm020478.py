def _mocked_device(
    device_config=DEVICE_CONFIG_LEGACY,
    credentials_hash=CREDENTIALS_HASH_LEGACY,
    mac=MAC_ADDRESS,
    device_id=DEVICE_ID,
    alias=ALIAS,
    model=MODEL,
    ip_address: str | None = None,
    modules: list[str] | None = None,
    children: list[Device] | None = None,
    features: list[str | Feature] | None = None,
    device_type=None,
    spec: type = Device,
) -> Device:
    device = MagicMock(spec=spec, name="Mocked device")
    device.update = AsyncMock()
    device.turn_off = AsyncMock()
    device.turn_on = AsyncMock()

    device.mac = mac
    device.alias = alias
    device.model = model
    device.device_id = device_id
    device.hw_info = {"sw_ver": "1.0.0", "hw_ver": "1.0.0"}
    device.modules = {}
    device.features = {}

    # replace device_config to prevent changes affecting between tests
    device_config = replace(device_config)

    if not ip_address:
        ip_address = IP_ADDRESS
    else:
        device_config.host = ip_address
    device.host = ip_address

    device_features = {}
    if features:
        device_features = {
            feature_id: _mocked_feature(feature_id, require_fixture=True)
            for feature_id in features
            if isinstance(feature_id, str)
        }

        device_features.update(
            {
                feature.id: feature
                for feature in features
                if isinstance(feature, Feature)
            }
        )
    device.features = device_features

    # Add modules after features so modules can add any required features
    if modules:
        device.modules = {
            module_name: MODULE_TO_MOCK_GEN[module_name](device)
            for module_name in modules
        }

    # module features are accessed from a module via get_feature which is
    # keyed on the module attribute name. Usually this is the same as the
    # feature.id but not always so accept overrides.
    module_features = {
        mod_key if (mod_key := v.expected_module_key) else k: v
        for k, v in device_features.items()
    }
    for mod in device.modules.values():
        # Some tests remove the feature from device_features to test missing
        # features, so check the key is still present there.
        mod.get_feature.side_effect = lambda mod_id: (
            mod_feat
            if (mod_feat := module_features.get(mod_id))
            and mod_feat.id in device_features
            else None
        )
        mod.has_feature.side_effect = lambda mod_id: (
            (mod_feat := module_features.get(mod_id)) and mod_feat.id in device_features
        )

    device.parent = None
    device.children = []
    if children:
        for child in children:
            child.mac = mac
            child.parent = device
        device.children = children
    device.device_type = device_type or DeviceType.Unknown
    if (
        not device_type
        and device.children
        and all(
            child.device_type is DeviceType.StripSocket for child in device.children
        )
    ):
        device.device_type = DeviceType.Strip

    device.protocol = _mock_protocol()
    device.config = device_config
    device.credentials_hash = credentials_hash

    return device