def _serve_object(
        self, request: Request, bucket_name: BucketName, path: str = None
    ) -> Response:
        """
        Serves the S3 Object as a website handler. It will match routing rules set in the configuration first,
        and redirect the request if necessary. They are specific case for handling configured index, see the docs:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/IndexDocumentSupport.html
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/CustomErrorDocSupport.html
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html
        :param request: Request object received by the router
        :param bucket_name: bucket name contained in the host name
        :param path: path of the request, corresponds to the S3 Object key
        :return: Response object, either the Object, a redirection or an error
        """

        website_config = self.s3_client.get_bucket_website(Bucket=bucket_name)
        headers = {}

        redirection = website_config.get("RedirectAllRequestsTo")
        if redirection:
            parsed_url = urlparse(request.url)
            redirect_to = request.url.replace(parsed_url.netloc, redirection["HostName"])
            if protocol := redirection.get("Protocol"):
                redirect_to = redirect_to.replace(parsed_url.scheme, protocol)

            headers["Location"] = redirect_to
            return Response("", status=301, headers=headers)

        object_key = path
        routing_rules = website_config.get("RoutingRules")
        # checks for prefix rules, before trying to get the key
        if (
            object_key
            and routing_rules
            and (rule := self._find_matching_rule(routing_rules, object_key=object_key))
        ):
            redirect_response = self._get_redirect_from_routing_rule(request, rule)
            return redirect_response

        # if the URL ends with a trailing slash, try getting the index first
        is_folder = request.url[-1] == "/"
        if (
            not object_key or is_folder
        ):  # the path automatically remove the trailing slash, even with strict_slashes=False
            index_key = website_config["IndexDocument"]["Suffix"]
            object_key = f"{object_key}{index_key}" if object_key else index_key

        try:
            s3_object = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
        except self.s3_client.exceptions.NoSuchKey:
            if not is_folder:
                # try appending the index suffix in case we're accessing a "folder" without a trailing slash
                index_key = website_config["IndexDocument"]["Suffix"]
                try:
                    self.s3_client.head_object(Bucket=bucket_name, Key=f"{object_key}/{index_key}")
                    return Response("", status=302, headers={"Location": f"/{object_key}/"})
                except self.s3_client.exceptions.ClientError:
                    pass

            # checks for error code (and prefix) rules, after trying to get the key
            if routing_rules and (
                rule := self._find_matching_rule(
                    routing_rules, object_key=object_key, error_code=404
                )
            ):
                redirect_response = self._get_redirect_from_routing_rule(request, rule)
                return redirect_response

            # tries to get the error document, otherwise raises NoSuchKey
            if error_document := website_config.get("ErrorDocument"):
                return self._return_error_document(
                    error_document=error_document,
                    bucket=bucket_name,
                    missing_key=object_key,
                )
            else:
                # If not ErrorDocument is configured, raise NoSuchKey
                raise

        if website_redirect_location := s3_object.get("WebsiteRedirectLocation"):
            headers["Location"] = website_redirect_location
            return Response("", status=301, headers=headers)

        if self._check_if_headers(request.headers, s3_object=s3_object):
            return Response("", status=304)

        headers = self._get_response_headers_from_object(s3_object)
        return Response(s3_object["Body"], headers=headers)