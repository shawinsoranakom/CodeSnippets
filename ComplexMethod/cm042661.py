def test_passing_objects_as_values(self):
        class TestPipeline:
            def process_item(self, i):
                return i

        settings = Settings(
            {
                "ITEM_PIPELINES": {
                    TestPipeline: 800,
                },
                "DOWNLOAD_HANDLERS": {
                    "ftp": FileDownloadHandler,
                },
            }
        )

        assert "ITEM_PIPELINES" in settings.attributes

        mypipeline, priority = settings.getdict("ITEM_PIPELINES").popitem()
        assert priority == 800
        assert mypipeline == TestPipeline
        assert isinstance(mypipeline(), TestPipeline)
        assert mypipeline().process_item("item") == "item"

        myhandler = settings.getdict("DOWNLOAD_HANDLERS").pop("ftp")
        assert myhandler == FileDownloadHandler
        myhandler_instance = build_from_crawler(myhandler, get_crawler())
        assert isinstance(myhandler_instance, FileDownloadHandler)
        assert hasattr(myhandler_instance, "download_request")