def svg_image():
    st.image(
        """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100" height="100">
        <clipPath id="clipCircle">
            <circle r="25" cx="25" cy="25"/>
        </clipPath>
        <image href="https://avatars.githubusercontent.com/karriebear" width="50" height="50" clip-path="url(#clipCircle)"/>
    </svg>
    """
    )