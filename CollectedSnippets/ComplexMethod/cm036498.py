def batch_make_image_embeddings(
    image_batches: list[Image.Image | list[Image.Image]],
    processor,
    llm: VllmRunner,
) -> list[Qwen2VLPromptImageEmbeddingInput]:
    """batched image embeddings for Qwen2-VL

    This will infer all images' embeddings in a single batch,
      and split the result according to input batches.

    image_batches:
      - Single-image batches: `list[Image.Image]`
      - Multiple-image batches: `list[list[Image.Image]]]`

    returns: `list[Qwen2VLPromptImageEmbeddingInput]`
    """

    image_batches_: list[Any] = image_batches[:]

    # convert single-image batches to multiple-image batches
    for idx in range(len(image_batches_)):
        if not isinstance(image_batches_[idx], list):
            image_batches_[idx] = [image_batches_[idx]]

        assert isinstance(image_batches_[idx], list)

    # append all images into a list (as a batch)
    images: list[Image.Image] = []
    for image_batch in image_batches_:
        images += image_batch

    # image to pixel values
    image_processor = processor.image_processor

    preprocess_result = image_processor.preprocess(
        images=images, return_tensors="pt"
    ).data
    pixel_values = preprocess_result["pixel_values"]
    image_grid_thw = preprocess_result["image_grid_thw"]

    # pixel values to embeddings & grid_thws
    def get_image_embeds(model):
        with torch.no_grad():
            visual = model.visual

            pixel_values_on_device = pixel_values.to(visual.device, dtype=visual.dtype)
            return visual(pixel_values_on_device, grid_thw=image_grid_thw).cpu()

    image_embeds = torch.concat(llm.apply_model(get_image_embeds))

    # split into original batches
    result: list[Qwen2VLPromptImageEmbeddingInput] = []
    image_counter = 0
    embed_counter = 0
    for image_batch in image_batches_:
        cur_batch_image_count = len(image_batch)
        merge_size = image_processor.merge_size
        cur_batch_embed_len = sum(
            grid_thw.prod(-1) // merge_size // merge_size
            for grid_thw in image_grid_thw[
                image_counter : image_counter + cur_batch_image_count
            ]
        )

        result.append(
            {
                "image_embeds": image_embeds[
                    embed_counter : embed_counter + cur_batch_embed_len
                ],
                "image_grid_thw": image_grid_thw[
                    image_counter : image_counter + cur_batch_image_count
                ],
            }
        )

        embed_counter += cur_batch_embed_len
        image_counter += cur_batch_image_count

    # ensure we don't lose any images or embeddings
    assert embed_counter == image_embeds.size(0)
    assert image_counter == image_grid_thw.size(0)
    assert len(image_batches) == len(result)

    return result