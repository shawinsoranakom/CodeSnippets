def save_api_request(endpoint: str, method: str, headers: Dict[str, str], body: Dict[str, Any], response: Optional[Dict[str, Any]] = None) -> str:
    """Save an API request to a JSON file."""

    # Check for duplicate requests (same URL and query)
    if endpoint in ["/scrape", "/scrape-with-llm"] and "url" in body and "query" in body:
        existing_requests = get_saved_requests()
        for existing_request in existing_requests:
            if (existing_request.endpoint == endpoint and 
                existing_request.body.get("url") == body["url"] and 
                existing_request.body.get("query") == body["query"]):
                print(f"Duplicate request found for URL: {body['url']} and query: {body['query']}")
                return existing_request.id  # Return existing request ID instead of creating new one

    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    saved_request = SavedApiRequest(
        id=request_id,
        endpoint=endpoint,
        method=method,
        headers=headers,
        body=body,
        timestamp=datetime.now().isoformat(),
        response=response
    )

    file_path = os.path.join("saved_requests", f"{request_id}.json")
    with open(file_path, "w") as f:
        json.dump(saved_request.dict(), f, indent=2)

    return request_id