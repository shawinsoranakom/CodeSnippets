def __init__(self) -> None:
        self.last_query_cost: int = 1
        self.remaining_points: int = 5000
        self.reset_at: datetime = datetime.fromtimestamp(0, timezone.utc)
        self.last_request_start_time: datetime = datetime.fromtimestamp(0, timezone.utc)
        self.speed_multiplier: float = 1.0