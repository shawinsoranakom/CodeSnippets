def update_request_info(self, cost: int, remaining: int, reset_at: str) -> None:
        self.last_query_cost = cost
        self.remaining_points = remaining
        self.reset_at = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))