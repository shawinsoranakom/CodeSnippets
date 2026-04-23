def check_block_error_rates(self) -> str:
        """Check block error rates and send Discord alerts if thresholds are exceeded."""
        try:
            logger.info("Checking block error rates")

            # Get executions from the last 24 hours
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)

            # Use SQL aggregation to efficiently count totals and failures by block
            block_stats = self._get_block_stats_from_db(start_time, end_time)

            # For blocks with high error rates, fetch error samples
            threshold = self.config.block_error_rate_threshold
            for block_name, stats in block_stats.items():
                if stats.total_executions >= 10 and stats.error_rate >= threshold * 100:
                    # Only fetch error samples for blocks that exceed threshold
                    error_samples = self._get_error_samples_for_block(
                        stats.block_id, start_time, end_time, limit=3
                    )
                    stats.error_samples = error_samples

            # Check thresholds and send alerts
            critical_alerts = self._generate_critical_alerts(block_stats, threshold)

            if critical_alerts:
                msg = "Block Error Rate Alert:\n\n" + "\n\n".join(critical_alerts)
                self.notification_client.discord_system_alert(msg)
                logger.info(
                    f"Sent block error rate alert for {len(critical_alerts)} blocks"
                )
                return f"Alert sent for {len(critical_alerts)} blocks with high error rates"

            # If no critical alerts, check if we should show top blocks
            if self.include_top_blocks > 0:
                top_blocks_msg = self._generate_top_blocks_alert(
                    block_stats, start_time, end_time
                )
                if top_blocks_msg:
                    self.notification_client.discord_system_alert(top_blocks_msg)
                    logger.info("Sent top blocks summary")
                    return "Sent top blocks summary"

            logger.info("No blocks exceeded error rate threshold")
            return "No errors reported for today"

        except Exception as e:
            logger.exception(f"Error checking block error rates: {e}")

            error = Exception(f"Error checking block error rates: {e}")
            msg = str(error)
            sentry_capture_error(error)
            self.notification_client.discord_system_alert(msg)
            return msg