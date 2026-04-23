def test_route_request_any_is_last(
        self, deployment_with_any_routes, parse_handler_chain, get_invocation_context, addressing
    ):
        handler = InvocationRequestRouter()

        def handle(_request: Request) -> RestApiInvocationContext:
            _context = get_invocation_context(_request)
            _context.deployment = deployment_with_any_routes
            parse_handler_chain.handle(_context, Response())
            handler(parse_handler_chain, _context, Response())
            return _context

        request = Request(
            "GET",
            path=self.get_path_from_addressing("/foo", addressing),
        )
        context = handle(request)

        assert context.resource["path"] == "/foo"
        assert context.resource["resourceMethods"]["GET"]

        request = Request(
            "DELETE",
            path=self.get_path_from_addressing("/foo", addressing),
        )
        context = handle(request)

        assert context.resource["path"] == "/foo"
        assert context.resource["resourceMethods"]["ANY"]

        request = Request(
            "PUT",
            path=self.get_path_from_addressing("/foo/random-value", addressing),
        )

        context = handle(request)

        assert context.resource["path"] == "/foo/{param}"
        assert context.resource_method == context.resource["resourceMethods"]["PUT"]

        request = Request(
            "GET",
            path=self.get_path_from_addressing("/foo/random-value", addressing),
        )

        context = handle(request)

        assert context.resource["path"] == "/foo/{param}"
        assert context.resource_method == context.resource["resourceMethods"]["ANY"]