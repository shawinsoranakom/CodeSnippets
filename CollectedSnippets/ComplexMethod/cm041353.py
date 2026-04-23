def test_route_request_with_greedy_parameter(
        self, deployment_with_routes, parse_handler_chain, get_invocation_context, addressing
    ):
        # assert that a path which does not contain `/proxy/bar` will be routed to {proxy+}
        request = Request(
            "DELETE",
            path=self.get_path_from_addressing("/proxy/this/is/a/proxy/req2%Fuest", addressing),
        )
        router_handler = InvocationRequestRouter()

        context = get_invocation_context(request)
        context.deployment = deployment_with_routes

        parse_handler_chain.handle(context, Response())
        router_handler(parse_handler_chain, context, Response())

        assert context.resource["pathPart"] == "{proxy+}"
        assert context.resource["path"] == "/proxy/{proxy+}"
        # TODO: maybe assert more regarding the data inside Resource Methods, but we don't use it yet
        assert context.resource_method == context.resource["resourceMethods"]["DELETE"]

        assert context.invocation_request["path_parameters"] == {
            "proxy": "this/is/a/proxy/req2%Fuest"
        }

        # assert that a path which does contain `/proxy/bar` will be routed to `/proxy/bar/{param}` if it has only
        # one resource after `bar`
        request = Request(
            "DELETE",
            path=self.get_path_from_addressing("/proxy/bar/foobar", addressing),
        )
        context = get_invocation_context(request)
        context.deployment = deployment_with_routes

        parse_handler_chain.handle(context, Response())
        router_handler(parse_handler_chain, context, Response())

        assert context.resource["path"] == "/proxy/bar/{param}"
        assert context.invocation_request["path_parameters"] == {"param": "foobar"}

        # assert that a path which does contain `/proxy/bar` will be routed to {proxy+} if it does not conform to
        # `/proxy/bar/{param}`
        # TODO: validate this with AWS
        request = Request(
            "DELETE",
            path=self.get_path_from_addressing("/proxy/test2/is/a/proxy/req2%Fuest", addressing),
        )
        context = get_invocation_context(request)
        context.deployment = deployment_with_routes

        parse_handler_chain.handle(context, Response())
        router_handler(parse_handler_chain, context, Response())

        assert context.resource["path"] == "/proxy/{proxy+}"
        assert context.invocation_request["path_parameters"] == {
            "proxy": "test2/is/a/proxy/req2%Fuest"
        }