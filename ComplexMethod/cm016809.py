def test_jobs_api_sorting(
        self, client: ComfyClient, builder: GraphBuilder
    ):
        """Test jobs API sorting"""
        for _ in range(3):
            self._create_history_item(client, builder)

        desc_jobs = client.get_jobs(sort_order="desc")
        asc_jobs = client.get_jobs(sort_order="asc")

        if len(desc_jobs["jobs"]) >= 2:
            desc_times = [j["create_time"] for j in desc_jobs["jobs"] if j["create_time"]]
            asc_times = [j["create_time"] for j in asc_jobs["jobs"] if j["create_time"]]
            if len(desc_times) >= 2:
                assert desc_times == sorted(desc_times, reverse=True), "Desc should be newest first"
            if len(asc_times) >= 2:
                assert asc_times == sorted(asc_times), "Asc should be oldest first"