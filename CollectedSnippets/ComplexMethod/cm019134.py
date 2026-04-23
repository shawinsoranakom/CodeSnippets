def test_services_yaml_set_program_and_options_option_keys() -> None:
    """Test that all program keys in services.yaml exist in the translation map."""
    services = load_yaml_dict(f"{home_connect.__path__[0]}/services.yaml")
    groups = services["set_program_and_options"]["fields"]
    groups.pop("device_id")
    groups.pop("affects_to")
    groups.pop("program")
    for group in groups.values():
        for option, option_data in group["fields"].items():
            assert option in PROGRAM_ENUM_OPTIONS or option in PROGRAM_OPTIONS, (
                f"{option} is missing from both PROGRAM_ENUM_OPTIONS and PROGRAM_OPTIONS"
            )
            if option in PROGRAM_ENUM_OPTIONS:
                enum_values = set(PROGRAM_ENUM_OPTIONS[option][1])
                assert enum_values == set(
                    option_data["selector"]["select"]["options"]
                ), (
                    f"Options for {option} do not match between services.yaml and constants.py"
                )
                assert "example" in option_data, (
                    f"Example value for {option} is missing"
                )
                assert option_data["example"] in enum_values, (
                    f"Example value for {option} is not a valid option"
                )