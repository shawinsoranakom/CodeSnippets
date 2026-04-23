async def _gather_summary_data(
        self, user_id: str, event_type: NotificationType, params: BaseSummaryParams
    ) -> BaseSummaryData:
        """Gathers the data to build a summary notification"""

        logger.info(
            f"Gathering summary data for {user_id} and {event_type} with {params=}"
        )

        try:
            # Get summary data from the database
            summary_data = await get_database_manager_async_client(
                should_retry=False
            ).get_user_execution_summary_data(
                user_id=user_id,
                start_time=params.start_date,
                end_time=params.end_date,
            )

            # Extract data from summary
            total_credits_used = summary_data.total_credits_used
            total_executions = summary_data.total_executions
            most_used_agent = summary_data.most_used_agent
            successful_runs = summary_data.successful_runs
            failed_runs = summary_data.failed_runs
            total_execution_time = summary_data.total_execution_time
            average_execution_time = summary_data.average_execution_time
            cost_breakdown = summary_data.cost_breakdown

            if event_type == NotificationType.DAILY_SUMMARY and isinstance(
                params, DailySummaryParams
            ):
                return DailySummaryData(
                    total_credits_used=total_credits_used,
                    total_executions=total_executions,
                    most_used_agent=most_used_agent,
                    total_execution_time=total_execution_time,
                    successful_runs=successful_runs,
                    failed_runs=failed_runs,
                    average_execution_time=average_execution_time,
                    cost_breakdown=cost_breakdown,
                    date=params.date,
                )
            elif event_type == NotificationType.WEEKLY_SUMMARY and isinstance(
                params, WeeklySummaryParams
            ):
                return WeeklySummaryData(
                    total_credits_used=total_credits_used,
                    total_executions=total_executions,
                    most_used_agent=most_used_agent,
                    total_execution_time=total_execution_time,
                    successful_runs=successful_runs,
                    failed_runs=failed_runs,
                    average_execution_time=average_execution_time,
                    cost_breakdown=cost_breakdown,
                    start_date=params.start_date,
                    end_date=params.end_date,
                )
            else:
                raise ValueError("Invalid event type or params")

        except Exception as e:
            logger.warning(f"Failed to gather summary data: {e}")
            # Return sensible defaults in case of error
            if event_type == NotificationType.DAILY_SUMMARY and isinstance(
                params, DailySummaryParams
            ):
                return DailySummaryData(
                    total_credits_used=0.0,
                    total_executions=0,
                    most_used_agent="No data available",
                    total_execution_time=0.0,
                    successful_runs=0,
                    failed_runs=0,
                    average_execution_time=0.0,
                    cost_breakdown={},
                    date=params.date,
                )
            elif event_type == NotificationType.WEEKLY_SUMMARY and isinstance(
                params, WeeklySummaryParams
            ):
                return WeeklySummaryData(
                    total_credits_used=0.0,
                    total_executions=0,
                    most_used_agent="No data available",
                    total_execution_time=0.0,
                    successful_runs=0,
                    failed_runs=0,
                    average_execution_time=0.0,
                    cost_breakdown={},
                    start_date=params.start_date,
                    end_date=params.end_date,
                )
            else:
                raise ValueError("Invalid event type or params") from e