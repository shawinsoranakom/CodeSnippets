def async_check_scanning_mode(self, scanner: HaScanner) -> None:
        """Check if the scanner is running in passive mode when active mode is requested."""
        passive_mode_issue_id = f"bluetooth_adapter_passive_mode_{scanner.source}"

        # Check if scanner is NOT in passive mode when active mode was requested
        if not (
            scanner.requested_mode is BluetoothScanningMode.ACTIVE
            and scanner.current_mode is BluetoothScanningMode.PASSIVE
        ):
            # Delete passive mode issue if it exists and we're not in passive fallback
            ir.async_delete_issue(self.hass, DOMAIN, passive_mode_issue_id)
            return

        # Create repair issue for passive mode fallback
        adapter_name = adapter_human_name(
            scanner.adapter, scanner.mac_address or "00:00:00:00:00:00"
        )
        adapter_details = self._bluetooth_adapters.adapters.get(scanner.adapter)
        model = adapter_model(adapter_details) if adapter_details else None

        # Determine adapter type for specific instructions
        # Default to USB for any other type or unknown
        if adapter_details and adapter_details.get(ADAPTER_TYPE) == "uart":
            translation_key = "bluetooth_adapter_passive_mode_uart"
        else:
            translation_key = "bluetooth_adapter_passive_mode_usb"

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            passive_mode_issue_id,
            is_fixable=False,  # Requires a reboot or unplug
            severity=ir.IssueSeverity.WARNING,
            translation_key=translation_key,
            translation_placeholders={
                "adapter": adapter_name,
                "model": model or "Unknown",
            },
        )