def test_get_handler_file_from_name(self):
        assert ".build/handler.js" == get_handler_file_from_name(
            ".build/handler.execute", Runtime.nodejs16_x
        )
        assert "./.build/handler.execute" == get_handler_file_from_name(
            "./.build/handler.execute", Runtime.go1_x
        )
        assert "CSharpHandlers.dll" == get_handler_file_from_name(
            "./CSharpHandlers::AwsDotnetCsharp.Handler::CreateProfileAsync",
            Runtime.dotnetcore3_1,
        )
        assert "test/handler.rb" == get_handler_file_from_name(
            "test.handler.execute", Runtime.ruby3_2
        )
        assert "test.handler.execute" == get_handler_file_from_name(
            "test.handler.execute", Runtime.go1_x
        )
        assert "main" == get_handler_file_from_name("main", Runtime.go1_x)
        assert "../handler.py" == get_handler_file_from_name("../handler.execute")
        assert "bootstrap" == get_handler_file_from_name("", Runtime.provided)