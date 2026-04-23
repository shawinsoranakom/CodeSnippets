def test_protobuf_stats(self):
        """Stats requests are returned in OpenMetrics protobuf format
        if the request's Content-Type header is protobuf.
        """
        self.mock_stats = [
            CacheStat(
                category_name="st.singleton",
                cache_name="foo",
                byte_length=128,
            ),
            CacheStat(
                category_name="st.memo",
                cache_name="bar",
                byte_length=256,
            ),
        ]

        # Requests can have multiple Accept headers. Only one of them needs
        # to specify protobuf in order to get back protobuf.
        headers = HTTPHeaders()
        headers.add("Accept", "application/openmetrics-text")
        headers.add("Accept", "application/x-protobuf")
        headers.add("Accept", "text/html")

        response = self.fetch("/st-metrics", headers=headers)
        self.assertEqual(200, response.code)
        self.assertEqual("application/x-protobuf", response.headers.get("Content-Type"))

        metric_set = MetricSetProto()
        metric_set.ParseFromString(response.body)

        expected = {
            "metricFamilies": [
                {
                    "name": "cache_memory_bytes",
                    "type": "GAUGE",
                    "unit": "bytes",
                    "help": "Total memory consumed by a cache.",
                    "metrics": [
                        {
                            "labels": [
                                {"name": "cache_type", "value": "st.singleton"},
                                {"name": "cache", "value": "foo"},
                            ],
                            "metricPoints": [{"gaugeValue": {"intValue": "128"}}],
                        },
                        {
                            "labels": [
                                {"name": "cache_type", "value": "st.memo"},
                                {"name": "cache", "value": "bar"},
                            ],
                            "metricPoints": [{"gaugeValue": {"intValue": "256"}}],
                        },
                    ],
                }
            ]
        }

        self.assertEqual(expected, MessageToDict(metric_set))