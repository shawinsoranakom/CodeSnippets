def video(
        self,
        data: MediaData,
        format: str = "video/mp4",
        start_time: int = 0,
    ) -> "DeltaGenerator":
        """Display a video player.

        Parameters
        ----------
        data : str, bytes, BytesIO, numpy.ndarray, or file opened with
                io.open().
            Raw video data, filename, or URL pointing to a video to load.
            Includes support for YouTube URLs.
            Numpy arrays and raw data formats must include all necessary file
            headers to match specified file format.
        format : str
            The mime type for the video file. Defaults to 'video/mp4'.
            See https://tools.ietf.org/html/rfc4281 for more info.
        start_time: int
            The time from which this element should start playing.

        Example
        -------
        >>> video_file = open('myvideo.mp4', 'rb')
        >>> video_bytes = video_file.read()
        >>>
        >>> st.video(video_bytes)

        .. output::
           https://doc-video.streamlitapp.com/
           height: 700px

        .. note::
           Some videos may not display if they are encoded using MP4V (which is an export option in OpenCV), as this codec is
           not widely supported by browsers. Converting your video to H.264 will allow the video to be displayed in Streamlit.
           See this `StackOverflow post <https://stackoverflow.com/a/49535220/2394542>`_ or this
           `Streamlit forum post <https://discuss.streamlit.io/t/st-video-doesnt-show-opencv-generated-mp4/3193/2>`_
           for more information.

        """
        video_proto = VideoProto()
        coordinates = self.dg._get_delta_path_str()
        marshall_video(coordinates, video_proto, data, format, start_time)
        return self.dg._enqueue("video", video_proto)