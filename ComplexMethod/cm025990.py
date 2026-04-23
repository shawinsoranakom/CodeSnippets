def convert_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a config dict by replacing component consts with library consts."""
    my_map = {
        CONF_NAME: dyn_const.CONF_NAME,
        CONF_HOST: dyn_const.CONF_HOST,
        CONF_PORT: dyn_const.CONF_PORT,
        CONF_AUTO_DISCOVER: dyn_const.CONF_AUTO_DISCOVER,
        CONF_POLL_TIMER: dyn_const.CONF_POLL_TIMER,
    }
    result = convert_with_map(config, my_map)
    if CONF_AREA in config:
        result[dyn_const.CONF_AREA] = {
            area: convert_area(area_conf)
            for (area, area_conf) in config[CONF_AREA].items()
        }
    if CONF_DEFAULT in config:
        result[dyn_const.CONF_DEFAULT] = convert_default(config[CONF_DEFAULT])
    if CONF_ACTIVE in config:
        result[dyn_const.CONF_ACTIVE] = ACTIVE_MAP[config[CONF_ACTIVE]]
    if CONF_PRESET in config:
        result[dyn_const.CONF_PRESET] = {
            preset: convert_preset(preset_conf)
            for (preset, preset_conf) in config[CONF_PRESET].items()
        }
    if CONF_TEMPLATE in config:
        result[dyn_const.CONF_TEMPLATE] = {
            TEMPLATE_MAP[template]: convert_template(template_conf)
            for (template, template_conf) in config[CONF_TEMPLATE].items()
        }
    return result