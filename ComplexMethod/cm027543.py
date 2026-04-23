def update(self) -> None:
        """Get the latest data and updates the states."""
        self.data.update()
        stats = self.data.stats
        ticker = self.data.ticker

        sensor_type = self.entity_description.key
        if sensor_type == "exchangerate":
            self._attr_native_value = ticker[self._currency].p15min
            self._attr_native_unit_of_measurement = self._currency
        elif sensor_type == "trade_volume_btc":
            self._attr_native_value = f"{stats.trade_volume_btc:.1f}"
        elif sensor_type == "miners_revenue_usd":
            self._attr_native_value = f"{stats.miners_revenue_usd:.0f}"
        elif sensor_type == "btc_mined":
            self._attr_native_value = str(stats.btc_mined * 1e-8)
        elif sensor_type == "trade_volume_usd":
            self._attr_native_value = f"{stats.trade_volume_usd:.1f}"
        elif sensor_type == "difficulty":
            self._attr_native_value = f"{stats.difficulty:.0f}"
        elif sensor_type == "minutes_between_blocks":
            self._attr_native_value = f"{stats.minutes_between_blocks:.2f}"
        elif sensor_type == "number_of_transactions":
            self._attr_native_value = str(stats.number_of_transactions)
        elif sensor_type == "hash_rate":
            self._attr_native_value = f"{stats.hash_rate * 0.000001:.1f}"
        elif sensor_type == "timestamp":
            self._attr_native_value = stats.timestamp
        elif sensor_type == "mined_blocks":
            self._attr_native_value = str(stats.mined_blocks)
        elif sensor_type == "blocks_size":
            self._attr_native_value = f"{stats.blocks_size:.1f}"
        elif sensor_type == "total_fees_btc":
            self._attr_native_value = f"{stats.total_fees_btc * 1e-8:.2f}"
        elif sensor_type == "total_btc_sent":
            self._attr_native_value = f"{stats.total_btc_sent * 1e-8:.2f}"
        elif sensor_type == "estimated_btc_sent":
            self._attr_native_value = f"{stats.estimated_btc_sent * 1e-8:.2f}"
        elif sensor_type == "total_btc":
            self._attr_native_value = f"{stats.total_btc * 1e-8:.2f}"
        elif sensor_type == "total_blocks":
            self._attr_native_value = f"{stats.total_blocks:.0f}"
        elif sensor_type == "next_retarget":
            self._attr_native_value = f"{stats.next_retarget:.2f}"
        elif sensor_type == "estimated_transaction_volume_usd":
            self._attr_native_value = f"{stats.estimated_transaction_volume_usd:.2f}"
        elif sensor_type == "miners_revenue_btc":
            self._attr_native_value = f"{stats.miners_revenue_btc * 1e-8:.1f}"
        elif sensor_type == "market_price_usd":
            self._attr_native_value = f"{stats.market_price_usd:.2f}"