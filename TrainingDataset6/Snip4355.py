async def get(
        current_user: Annotated[DummyUser | None, Depends(get_current_user)],
    ) -> str:
        return "hello world"