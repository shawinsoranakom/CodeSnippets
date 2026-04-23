def _assert_subscription_order():
        discovery_subscribes = [
            f"homeassistant/{platform}/+/config" for platform in SUPPORTED_COMPONENTS
        ]
        discovery_subscribes.extend(
            [
                f"homeassistant/{platform}/+/+/config"
                for platform in SUPPORTED_COMPONENTS
            ]
        )
        discovery_subscribes.extend(
            ["homeassistant/device/+/config", "homeassistant/device/+/+/config"]
        )
        discovery_subscribes.extend(["integration/test#", "integration/kitchen_sink#"])

        expected_discovery_subscribes = discovery_subscribes.copy()

        # Assert we see the expected subscribes and in the correct order
        actual_subscribes = [
            discovery_subscribes.pop(0)
            for call in help_all_subscribe_calls(mqtt_client_mock)
            if discovery_subscribes and discovery_subscribes[0] == call[0]
        ]

        # Assert we have processed all items and that they are in the correct order
        assert len(discovery_subscribes) == 0
        assert actual_subscribes == expected_discovery_subscribes