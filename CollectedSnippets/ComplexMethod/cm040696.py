def event_for_lambda_url(api_id: str, request: Request) -> dict:
    partitioned_uri = request.full_path.partition("?")
    raw_path = partitioned_uri[0]
    raw_query_string = partitioned_uri[2]

    query_string_parameters = {k: ",".join(request.args.getlist(k)) for k in request.args.keys()}

    now = datetime.utcnow()
    readable = timestamp(time=now, format=TIMESTAMP_READABLE_FORMAT)
    if not any(char in readable for char in ["+", "-"]):
        readable += "+0000"

    data = restore_payload(request)
    headers = request.headers
    source_ip = headers.get("Remote-Addr", "")
    request_context = {
        "accountId": "anonymous",
        "apiId": api_id,
        "domainName": headers.get("Host", ""),
        "domainPrefix": api_id,
        "http": {
            "method": request.method,
            "path": raw_path,
            "protocol": "HTTP/1.1",
            "sourceIp": source_ip,
            "userAgent": headers.get("User-Agent", ""),
        },
        "requestId": long_uid(),
        "routeKey": "$default",
        "stage": "$default",
        "time": readable,
        "timeEpoch": mktime(ts=now, millis=True),
    }

    content_type = headers.get("Content-Type", "").lower()
    content_type_is_text = any(text_type in content_type for text_type in ["text", "json", "xml"])

    is_base64_encoded = not (data.isascii() and content_type_is_text) if data else False
    body = base64.b64encode(data).decode() if is_base64_encoded else data
    if isinstance(body, bytes):
        body = to_str(body)

    ignored_headers = ["connection", "x-localstack-tgt-api", "x-localstack-request-url"]
    event_headers = {k.lower(): v for k, v in headers.items() if k.lower() not in ignored_headers}

    event_headers.update(
        {
            "x-amzn-tls-cipher-suite": "ECDHE-RSA-AES128-GCM-SHA256",
            "x-amzn-tls-version": "TLSv1.2",
            "x-forwarded-proto": "http",
            "x-forwarded-for": source_ip,
            "x-forwarded-port": str(localstack_host().port),
        }
    )

    event = {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": raw_path,
        "rawQueryString": raw_query_string,
        "headers": event_headers,
        "queryStringParameters": query_string_parameters,
        "requestContext": request_context,
        "body": body,
        "isBase64Encoded": is_base64_encoded,
    }

    if not data:
        event.pop("body")

    return event