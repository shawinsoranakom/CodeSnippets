async def execute(
        cls,
        model_name: str,
        prompt: str,
        aspect_ratio: str,
        duration: int,
        resolution: str = "1080p",
        storyboards: dict | None = None,
        generate_audio: bool = False,
        seed: int = 0,
    ) -> IO.NodeOutput:
        _ = seed
        if model_name == "kling-video-o1":
            if duration not in (5, 10):
                raise ValueError("kling-video-o1 only supports durations of 5 or 10 seconds.")
            if generate_audio:
                raise ValueError("kling-video-o1 does not support audio generation.")
        stories_enabled = storyboards is not None and storyboards["storyboards"] != "disabled"
        if stories_enabled and model_name == "kling-video-o1":
            raise ValueError("kling-video-o1 does not support storyboards.")
        validate_string(prompt, strip_whitespace=True, min_length=0 if stories_enabled else 1, max_length=2500)

        multi_shot = None
        multi_prompt_list = None
        if stories_enabled:
            count = int(storyboards["storyboards"].split()[0])
            multi_shot = True
            multi_prompt_list = []
            for i in range(1, count + 1):
                sb_prompt = storyboards[f"storyboard_{i}_prompt"]
                sb_duration = storyboards[f"storyboard_{i}_duration"]
                validate_string(sb_prompt, field_name=f"storyboard_{i}_prompt", min_length=1, max_length=512)
                multi_prompt_list.append(
                    MultiPromptEntry(
                        index=i,
                        prompt=sb_prompt,
                        duration=str(sb_duration),
                    )
                )
            total_storyboard_duration = sum(int(e.duration) for e in multi_prompt_list)
            if total_storyboard_duration != duration:
                raise ValueError(
                    f"Total storyboard duration ({total_storyboard_duration}s) "
                    f"must equal the global duration ({duration}s)."
                )

        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/kling/v1/videos/omni-video", method="POST"),
            response_model=TaskStatusResponse,
            data=OmniProText2VideoRequest(
                model_name=model_name,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                duration=str(duration),
                mode="pro" if resolution == "1080p" else "std",
                multi_shot=multi_shot,
                multi_prompt=multi_prompt_list,
                shot_type="customize" if multi_shot else None,
                sound="on" if generate_audio else "off",
            ),
        )
        return await finish_omni_video_task(cls, response)