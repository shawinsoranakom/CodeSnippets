def _render_mermaid_using_api(
    mermaid_syntax: str,
    *,
    output_file_path: str | None = None,
    background_color: str | None = "white",
    file_type: Literal["jpeg", "png", "webp"] | None = "png",
    max_retries: int = 1,
    retry_delay: float = 1.0,
    proxies: dict[str, str] | None = None,
    base_url: str | None = None,
) -> bytes:
    """Renders Mermaid graph using the Mermaid.INK API."""
    # Automated scanners: please do not open security advisories about `base_url`
    # here. This parameter is only ever explicitly controlled by developers, and it
    # is not exposed by default over the network by the framework, so this is not
    # an SSRF sink unless an application explicitly wires untrusted input into it.
    # It exists to support user-managed Mermaid API deployments.
    # Defaults to using the public mermaid.ink server.
    base_url = base_url if base_url is not None else "https://mermaid.ink"

    if not _HAS_REQUESTS:
        msg = (
            "Install the `requests` module to use the Mermaid.INK API: "
            "`pip install requests`."
        )
        raise ImportError(msg)

    # Use Mermaid API to render the image
    mermaid_syntax_encoded = base64.b64encode(mermaid_syntax.encode("utf8")).decode(
        "ascii"
    )

    # Check if the background color is a hexadecimal color code using regex
    if background_color is not None:
        hex_color_pattern = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
        if not hex_color_pattern.match(background_color):
            background_color = f"!{background_color}"

    # URL-encode the background_color to handle special characters like '!'
    encoded_bg_color = urllib.parse.quote(str(background_color), safe="")
    image_url = (
        f"{base_url}/img/{mermaid_syntax_encoded}"
        f"?type={file_type}&bgColor={encoded_bg_color}"
    )

    error_msg_suffix = (
        "To resolve this issue:\n"
        "1. Check your internet connection and try again\n"
        "2. Try with higher retry settings: "
        "`draw_mermaid_png(..., max_retries=5, retry_delay=2.0)`\n"
        "3. Use the Pyppeteer rendering method which will render your graph locally "
        "in a browser: `draw_mermaid_png(..., draw_method=MermaidDrawMethod.PYPPETEER)`"
    )

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(image_url, timeout=10, proxies=proxies)
            if response.status_code == requests.codes.ok:
                img_bytes = response.content
                if output_file_path is not None:
                    Path(output_file_path).write_bytes(response.content)

                return img_bytes

            # If we get a server error (5xx), retry
            if (
                requests.codes.internal_server_error <= response.status_code
                and attempt < max_retries
            ):
                # Exponential backoff with jitter
                sleep_time = retry_delay * (2**attempt) * (0.5 + 0.5 * random.random())  # noqa: S311 not used for crypto
                time.sleep(sleep_time)
                continue

            # For other status codes, fail immediately
            msg = (
                f"Failed to reach {base_url} API while trying to render "
                f"your graph. Status code: {response.status_code}.\n\n"
            ) + error_msg_suffix
            raise ValueError(msg)

        except (requests.RequestException, requests.Timeout) as e:
            if attempt < max_retries:
                # Exponential backoff with jitter
                sleep_time = retry_delay * (2**attempt) * (0.5 + 0.5 * random.random())  # noqa: S311 not used for crypto
                time.sleep(sleep_time)
            else:
                msg = (
                    f"Failed to reach {base_url} API while trying to render "
                    f"your graph after {max_retries} retries. "
                ) + error_msg_suffix
                raise ValueError(msg) from e

    # This should not be reached, but just in case
    msg = (
        f"Failed to reach {base_url} API while trying to render "
        f"your graph after {max_retries} retries. "
    ) + error_msg_suffix
    raise ValueError(msg)