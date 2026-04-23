def test_camel_to_snake_case(self):
        fn = common.camel_to_snake_case

        assert fn("Foo") == "foo"
        assert fn("FoobarEd") == "foobar_ed"
        assert fn("FooBarEd") == "foo_bar_ed"
        assert fn("Foo_Bar") == "foo_bar"
        assert fn("Foo__Bar") == "foo__bar"
        assert fn("FooBAR") == "foo_bar"
        assert fn("HTTPRequest") == "http_request"
        assert fn("HTTP_Request") == "http_request"
        assert fn("VerifyHTTPRequest") == "verify_http_request"
        assert fn("IsHTTP") == "is_http"
        assert fn("IsHTTP2Request") == "is_http2_request"