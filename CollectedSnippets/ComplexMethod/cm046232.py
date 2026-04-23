def get_best_youtube_url(url: str, method: str = "pytube") -> str | None:
    """Retrieve the URL of the best quality MP4 video stream from a given YouTube video.

    Args:
        url (str): The URL of the YouTube video.
        method (str): The method to use for extracting video info. Options are "pytube", "pafy", and "yt-dlp".

    Returns:
        (str | None): The URL of the best quality MP4 video stream, or None if no suitable stream is found.

    Examples:
        >>> url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        >>> best_url = get_best_youtube_url(url)
        >>> print(best_url)
        https://rr4---sn-q4flrnek.googlevideo.com/videoplayback?expire=...

    Notes:
        - Requires additional libraries based on the chosen method: pytubefix, pafy, or yt-dlp.
        - The function prioritizes streams with at least 1080p resolution when available.
        - For the "yt-dlp" method, it looks for formats with video codec, no audio, and *.mp4 extension.
    """
    if method == "pytube":
        # Switched from pytube to pytubefix to resolve https://github.com/pytube/pytube/issues/1954
        check_requirements("pytubefix>=6.5.2")
        from pytubefix import YouTube

        streams = YouTube(url).streams.filter(file_extension="mp4", only_video=True)
        streams = sorted(streams, key=lambda s: s.resolution, reverse=True)  # sort streams by resolution
        for stream in streams:
            if stream.resolution and int(stream.resolution[:-1]) >= 1080:  # check if resolution is at least 1080p
                return stream.url

    elif method == "pafy":
        check_requirements(("pafy", "youtube_dl==2020.12.2"))
        import pafy

        return pafy.new(url).getbestvideo(preftype="mp4").url

    elif method == "yt-dlp":
        check_requirements("yt-dlp")
        import yt_dlp

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)  # extract info
        for f in reversed(info_dict.get("formats", [])):  # reversed because best is usually last
            # Find a format with video codec, no audio, *.mp4 extension at least 1920x1080 size
            good_size = (f.get("width") or 0) >= 1920 or (f.get("height") or 0) >= 1080
            if good_size and f["vcodec"] != "none" and f["acodec"] == "none" and f["ext"] == "mp4":
                return f.get("url")