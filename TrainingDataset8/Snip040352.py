def get_app(self):
        self.mock_stats = []
        mock_stats_manager = MagicMock()
        mock_stats_manager.get_stats = MagicMock(side_effect=lambda: self.mock_stats)
        return tornado.web.Application(
            [
                (
                    r"/st-metrics",
                    StatsRequestHandler,
                    dict(stats_manager=mock_stats_manager),
                )
            ]
        )