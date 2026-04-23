def batch_make_video_embeddings(
    video_batches: PromptVideoInput, processor, llm: VllmRunner
) -> list[Qwen2VLPromptVideoEmbeddingInput]:
    """batched video embeddings for Qwen2-VL

    A NDArray represents a single video's all frames.

    This will infer all videos' embeddings in a single batch,
      and split the result according to input batches.

    video_batches:
      - Single-video batches: `list[NDArray]`
      - Multiple-video batches: `list[list[NDArray]]`
    """

    video_batches_: list[Any] = video_batches[:]

    for idx in range(len(video_batches_)):
        if not isinstance(video_batches_[idx], list):
            single_video_batch: list[npt.NDArray] = [video_batches_[idx]]
            video_batches_[idx] = single_video_batch

        assert isinstance(video_batches_[idx], list)

    # append all videos into a list (as a batch)
    videos: list[npt.NDArray] = []
    for video_batch in video_batches_:
        videos += video_batch

    # video to pixel values
    video_processor = processor.video_processor

    preprocess_result = video_processor.preprocess(
        videos=videos, return_tensors="pt"
    ).data
    pixel_values = preprocess_result["pixel_values_videos"]
    video_grid_thw = preprocess_result["video_grid_thw"]

    # pixel values to embeddings & grid_thws
    def get_image_embeds(model):
        with torch.no_grad():
            visual = model.visual

            pixel_values_on_device = pixel_values.to(visual.device, dtype=visual.dtype)
            return visual(pixel_values_on_device, grid_thw=video_grid_thw).cpu()

    video_embeds = torch.concat(llm.apply_model(get_image_embeds))

    # split into original batches
    result: list[Qwen2VLPromptVideoEmbeddingInput] = []
    video_counter = 0
    embed_counter = 0
    for video_batch in video_batches_:
        cur_batch_video_count = len(video_batch)
        merge_size = video_processor.merge_size
        cur_batch_embed_len = sum(
            grid_thw.prod(-1) // merge_size // merge_size
            for grid_thw in video_grid_thw[
                video_counter : video_counter + cur_batch_video_count
            ]
        )

        result.append(
            {
                "video_embeds": video_embeds[
                    embed_counter : embed_counter + cur_batch_embed_len
                ],
                "video_grid_thw": video_grid_thw[
                    video_counter : video_counter + cur_batch_video_count
                ],
            }
        )

        embed_counter += cur_batch_embed_len
        video_counter += cur_batch_video_count

    # ensure we don't lose any videos or embeddings
    assert embed_counter == video_embeds.size(0)
    assert video_counter == video_grid_thw.size(0)
    assert len(video_batches) == len(result)

    return result