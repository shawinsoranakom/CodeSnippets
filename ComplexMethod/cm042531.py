def _assert_downloaded_responses(run: CrawlerRun, count: int) -> None:
        # response tests
        assert len(run.respplug) == count
        assert len(run.reqreached) == count

        for response, _ in run.respplug:
            if run.getpath(response.url) == "/static/item999.html":
                assert response.status == 404
            if run.getpath(response.url) == "/redirect":
                assert response.status == 302