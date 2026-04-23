async def create_post(
    credentials: Credentials,
    site: str,
    post_data: CreatePostRequest,
) -> PostResponse:
    """
    Create a new post on a WordPress site.

    Args:
        site: Site ID or domain (e.g., "myblog.wordpress.com" or "123456789")
        access_token: OAuth access token
        post_data: Post data using CreatePostRequest model

    Returns:
        PostResponse with the created post details
    """

    # Convert the post data to a dictionary, excluding None values
    data = post_data.model_dump(exclude_none=True)

    # Handle special fields that need conversion
    if "categories" in data and isinstance(data["categories"], list):
        data["categories"] = ",".join(str(c) for c in data["categories"])

    if "tags" in data and isinstance(data["tags"], list):
        data["tags"] = ",".join(str(t) for t in data["tags"])

    # Make the API request
    site = normalize_site(site)
    endpoint = f"/rest/v1.1/sites/{site}/posts/new"

    headers = {
        "Authorization": credentials.auth_header(),
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = await Requests(raise_for_status=False).post(
        f"{WORDPRESS_BASE_URL.rstrip('/')}{endpoint}",
        headers=headers,
        data=data,
    )

    if response.ok:
        return PostResponse.model_validate(response.json())

    error_data = (
        response.json()
        if response.headers.get("content-type", "").startswith("application/json")
        else {}
    )
    error_message = error_data.get("message", response.text)
    raise ValueError(f"Failed to create post: {response.status} - {error_message}")