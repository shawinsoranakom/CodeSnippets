def processor(*args, videos=None, **kwargs):
        if videos is not None and is_list_of(videos, tuple):
            # batched multi videos
            do_sample_frames = {video[1]["do_sample_frames"] for video in videos}
            assert len(do_sample_frames) == 1
            if kwargs.get("do_sample_frames") is None:
                kwargs["do_sample_frames"] = do_sample_frames
            video_metadata = [
                [
                    VideoMetadata(
                        **{k: v for k, v in video[1].items() if k != "do_sample_frames"}
                    )
                ]
                for video in videos
            ]
            videos = [[video[0]] for video in videos]
        elif videos is not None and isinstance(videos, tuple):
            # single video
            do_sample_frames = videos[1]["do_sample_frames"]
            if kwargs.get("do_sample_frames") is None:
                kwargs["do_sample_frames"] = do_sample_frames
            video_metadata = [
                [
                    VideoMetadata(
                        **{
                            k: v
                            for k, v in videos[1].items()
                            if k != "do_sample_frames"
                        }
                    )
                ]
            ]
            videos = [[videos[0]]]
        else:
            video_metadata = None

        return hf_processor(
            *args, videos=videos, video_metadata=video_metadata, **kwargs
        )