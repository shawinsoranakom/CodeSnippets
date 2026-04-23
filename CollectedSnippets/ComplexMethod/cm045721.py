async def _parse_b64_images(
    b64_images: list[str],
    llm: pw.UDF,
    parse_prompt: str,
    *,
    run_mode: Literal["sequential", "parallel"],
    parse_details: bool,
    detail_parse_schema: type[BaseModel] | None,
    parse_fn: Callable,
    parse_image_details_fn: Callable | None,
) -> tuple[list[str], list[BaseModel]]:
    total_images = len(b64_images)

    if parse_details:
        assert detail_parse_schema is not None and issubclass(
            detail_parse_schema, BaseModel
        ), "`detail_parse_schema` must be valid Pydantic Model class when `parse_details` is True"

    logger.info(f"`parse_images` parsing descriptions for {total_images} images.")

    parsed_details: list[BaseModel] = []

    if run_mode == "sequential":
        parsed_content = []

        for img in b64_images:
            parsed_txt = await parse_fn(img, llm, parse_prompt)
            parsed_content.append(parsed_txt)

        if parse_details:
            assert parse_image_details_fn is not None
            parsed_details = []
            for img in b64_images:
                parsed_detail = await parse_image_details_fn(
                    img,
                    parse_schema=detail_parse_schema,
                )
                parsed_details.append(parsed_detail)

    else:
        parse_tasks = [parse_fn(img, llm, parse_prompt) for img in b64_images]

        if parse_details:
            assert parse_image_details_fn is not None
            detail_tasks = [
                parse_image_details_fn(
                    img,
                    parse_schema=detail_parse_schema,
                )
                for img in b64_images
            ]
        else:
            detail_tasks = []

        results = await asyncio.gather(*parse_tasks, *detail_tasks)

        parsed_content = results[: len(b64_images)]
        parsed_details = results[len(b64_images) :]

    return parsed_content, parsed_details