async def create_shop(
    data: Shop = Body(media_type=media_type),
    included: list[Product] = Body(default=[], media_type=media_type),
):
    pass