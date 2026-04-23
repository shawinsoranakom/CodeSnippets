def save_union_body_discriminator(
        item: Item, q: Annotated[str, Field(description="Query string")]
    ) -> dict[str, Any]:
        return {"item": item}