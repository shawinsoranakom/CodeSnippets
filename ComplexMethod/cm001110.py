def check_execution_accuracy_alerts(self) -> str:
        """Check marketplace agents for accuracy drops and send alerts."""
        try:
            logger.info("Checking execution accuracy for marketplace agents")

            # Get marketplace graphs using database client
            graphs = self.database_client.get_marketplace_graphs_for_monitoring(
                days_back=30, min_executions=10
            )

            alerts_found = 0

            for graph_data in graphs:
                result = self.database_client.get_accuracy_trends_and_alerts(
                    graph_id=graph_data.graph_id,
                    user_id=graph_data.user_id,
                    days_back=21,  # 3 weeks
                    drop_threshold=self.drop_threshold,
                )

                if result.alert:
                    alert = result.alert

                    # Get graph details for better alert info
                    try:
                        graph_info = self.database_client.get_graph_metadata(
                            graph_id=alert.graph_id
                        )
                        graph_name = graph_info.name if graph_info else "Unknown Agent"
                    except Exception:
                        graph_name = "Unknown Agent"

                    # Create detailed alert message
                    alert_msg = (
                        f"🚨 **AGENT ACCURACY DROP DETECTED**\n\n"
                        f"**Agent:** {graph_name}\n"
                        f"**Graph ID:** `{alert.graph_id}`\n"
                        f"**Accuracy Drop:** {alert.drop_percent:.1f}%\n"
                        f"**Recent Performance:**\n"
                        f"  • 3-day average: {alert.three_day_avg:.1f}%\n"
                        f"  • 7-day average: {alert.seven_day_avg:.1f}%\n"
                    )

                    if alert.user_id:
                        alert_msg += f"**Owner:** {alert.user_id}\n"

                    # Send individual alert for each agent (not batched)
                    self.notification_client.discord_system_alert(
                        alert_msg, DiscordChannel.PRODUCT
                    )
                    alerts_found += 1
                    logger.warning(
                        f"Sent accuracy alert for agent: {graph_name} ({alert.graph_id})"
                    )

            if alerts_found > 0:
                return f"Alert sent for {alerts_found} agents with accuracy drops"

            logger.info("No execution accuracy alerts detected")
            return "No accuracy alerts detected"

        except Exception as e:
            logger.exception(f"Error checking execution accuracy alerts: {e}")

            error = Exception(f"Error checking execution accuracy alerts: {e}")
            msg = str(error)
            sentry_capture_error(error)
            self.notification_client.discord_system_alert(msg, DiscordChannel.PRODUCT)
            return msg