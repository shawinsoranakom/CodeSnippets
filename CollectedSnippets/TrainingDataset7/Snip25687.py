def test_multi_part_parser_error(self):
        self.assertLogsRequest(
            url="/multi_part_parser_error/",
            level="WARNING",
            status_code=400,
            msg="Bad request (Unable to parse request body): /multi_part_parser_error/",
            exc_class=MultiPartParserError,
        )