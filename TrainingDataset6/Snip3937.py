def main(request: Request) -> dict[str, str]:
        assert request.state.app
        assert request.state.router
        assert request.state.sub_router
        return {"message": "Hello World"}