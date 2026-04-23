def get_template_body(req_data: dict) -> str:
    body = req_data.get("TemplateBody")
    if body:
        return body
    url = req_data.get("TemplateURL")
    if url:
        response = run_safe(lambda: safe_requests.get(url, verify=False))
        # check error codes, and code 301 - fixes https://github.com/localstack/localstack/issues/1884
        status_code = 0 if response is None else response.status_code
        if response is None or status_code == 301 or status_code >= 400:
            # check if this is an S3 URL, then get the file directly from there
            url = convert_s3_to_local_url(url)
            if is_local_service_url(url):
                parsed_path = urlparse(url).path.lstrip("/")
                parts = parsed_path.partition("/")
                client = connect_to().s3
                LOG.debug(
                    "Download CloudFormation template content from local S3: %s - %s",
                    parts[0],
                    parts[2],
                )
                result = client.get_object(Bucket=parts[0], Key=parts[2])
                body = to_str(result["Body"].read())
                return body
            raise Exception(f"Unable to fetch template body (code {status_code}) from URL {url}")
        return to_str(response.content)
    raise Exception(f"Unable to get template body from input: {req_data}")