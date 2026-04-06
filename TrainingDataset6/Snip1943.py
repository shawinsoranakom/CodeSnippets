def __enter__(self) -> "RateLimiter":
        now = datetime.now(tz=timezone.utc)

        # Handle primary rate limits
        primary_limit_wait_time = 0.0
        if self.remaining_points <= self.last_query_cost:
            primary_limit_wait_time = (self.reset_at - now).total_seconds() + 2
            logging.warning(
                f"Approaching GitHub API rate limit, remaining points: {self.remaining_points}, "
                f"reset time in {primary_limit_wait_time} seconds"
            )

        # Handle secondary rate limits
        secondary_limit_wait_time = 0.0
        points_per_minute = POINTS_PER_MINUTE_LIMIT * self.speed_multiplier
        interval = 60 / (points_per_minute / self.last_query_cost)
        time_since_last_request = (now - self.last_request_start_time).total_seconds()
        if time_since_last_request < interval:
            secondary_limit_wait_time = interval - time_since_last_request

        final_wait_time = ceil(max(primary_limit_wait_time, secondary_limit_wait_time))
        logging.info(f"Sleeping for {final_wait_time} seconds to respect rate limit")
        time.sleep(max(final_wait_time, 1))

        self.last_request_start_time = datetime.now(tz=timezone.utc)
        return self