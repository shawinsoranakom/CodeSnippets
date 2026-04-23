async def run(
        self,
        input_data: Input,
        *,
        execution_context: ExecutionContext,
        **kwargs,
    ) -> BlockOutput:
        assert execution_context.graph_exec_id is not None
        assert execution_context.node_exec_id is not None
        graph_exec_id = execution_context.graph_exec_id
        node_exec_id = execution_context.node_exec_id

        # 1) Store the input video locally
        local_video_path = await store_media_file(
            file=input_data.video_in,
            execution_context=execution_context,
            return_format="for_local_processing",
        )
        input_abspath = get_exec_file_path(graph_exec_id, local_video_path)

        # 2) Load the clip
        strip_chapters_inplace(input_abspath)
        clip = None
        looped_clip = None
        try:
            clip = VideoFileClip(input_abspath)

            # 3) Apply the loop effect
            if input_data.duration:
                # Loop until we reach the specified duration
                looped_clip = clip.with_effects([Loop(duration=input_data.duration)])
            elif input_data.n_loops:
                looped_clip = clip.with_effects([Loop(n=input_data.n_loops)])
            else:
                raise ValueError("Either 'duration' or 'n_loops' must be provided.")

            assert isinstance(looped_clip, VideoFileClip)

            # 4) Save the looped output
            source = extract_source_name(local_video_path)
            output_filename = MediaFileType(f"{node_exec_id}_looped_{source}.mp4")
            output_abspath = get_exec_file_path(graph_exec_id, output_filename)

            looped_clip = looped_clip.with_audio(clip.audio)
            looped_clip.write_videofile(
                output_abspath, codec="libx264", audio_codec="aac"
            )
        finally:
            if looped_clip:
                looped_clip.close()
            if clip:
                clip.close()

        # Return output - for_block_output returns workspace:// if available, else data URI
        video_out = await store_media_file(
            file=output_filename,
            execution_context=execution_context,
            return_format="for_block_output",
        )

        yield "video_out", video_out