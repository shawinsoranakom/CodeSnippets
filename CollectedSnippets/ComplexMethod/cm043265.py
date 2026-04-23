async def validate(
        self,
        url: str,
        stored_etag: Optional[str] = None,
        stored_last_modified: Optional[str] = None,
        stored_head_fingerprint: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate if cached content is still fresh.

        Args:
            url: The URL to validate
            stored_etag: Previously stored ETag header value
            stored_last_modified: Previously stored Last-Modified header value
            stored_head_fingerprint: Previously computed head fingerprint

        Returns:
            ValidationResult with status and any updated metadata
        """
        client = await self._get_client()

        # Build conditional request headers
        headers = {}
        if stored_etag:
            headers["If-None-Match"] = stored_etag
        if stored_last_modified:
            headers["If-Modified-Since"] = stored_last_modified

        try:
            # Step 1: Try HEAD request with conditional headers
            if headers:
                response = await client.head(url, headers=headers)

                if response.status_code == 304:
                    return ValidationResult(
                        status=CacheValidationResult.FRESH,
                        reason="Server returned 304 Not Modified"
                    )

                # Got 200, extract new headers for potential update
                new_etag = response.headers.get("etag")
                new_last_modified = response.headers.get("last-modified")

                # If we have fingerprint, compare it
                if stored_head_fingerprint:
                    head_html, _, _ = await self._fetch_head(url)
                    if head_html:
                        new_fingerprint = compute_head_fingerprint(head_html)
                        if new_fingerprint and new_fingerprint == stored_head_fingerprint:
                            return ValidationResult(
                                status=CacheValidationResult.FRESH,
                                new_etag=new_etag,
                                new_last_modified=new_last_modified,
                                new_head_fingerprint=new_fingerprint,
                                reason="Head fingerprint matches"
                            )
                        elif new_fingerprint:
                            return ValidationResult(
                                status=CacheValidationResult.STALE,
                                new_etag=new_etag,
                                new_last_modified=new_last_modified,
                                new_head_fingerprint=new_fingerprint,
                                reason="Head fingerprint changed"
                            )

                # Headers changed and no fingerprint match
                return ValidationResult(
                    status=CacheValidationResult.STALE,
                    new_etag=new_etag,
                    new_last_modified=new_last_modified,
                    reason="Server returned 200, content may have changed"
                )

            # Step 2: No conditional headers available, try fingerprint only
            if stored_head_fingerprint:
                head_html, new_etag, new_last_modified = await self._fetch_head(url)

                if head_html:
                    new_fingerprint = compute_head_fingerprint(head_html)

                    if new_fingerprint and new_fingerprint == stored_head_fingerprint:
                        return ValidationResult(
                            status=CacheValidationResult.FRESH,
                            new_etag=new_etag,
                            new_last_modified=new_last_modified,
                            new_head_fingerprint=new_fingerprint,
                            reason="Head fingerprint matches"
                        )
                    elif new_fingerprint:
                        return ValidationResult(
                            status=CacheValidationResult.STALE,
                            new_etag=new_etag,
                            new_last_modified=new_last_modified,
                            new_head_fingerprint=new_fingerprint,
                            reason="Head fingerprint changed"
                        )

            # Step 3: No validation data available
            return ValidationResult(
                status=CacheValidationResult.UNKNOWN,
                reason="No validation data available (no etag, last-modified, or fingerprint)"
            )

        except httpx.TimeoutException:
            return ValidationResult(
                status=CacheValidationResult.ERROR,
                reason="Validation request timed out"
            )
        except httpx.RequestError as e:
            return ValidationResult(
                status=CacheValidationResult.ERROR,
                reason=f"Validation request failed: {type(e).__name__}"
            )
        except Exception as e:
            # On unexpected error, prefer using cache over failing
            return ValidationResult(
                status=CacheValidationResult.ERROR,
                reason=f"Validation error: {str(e)}"
            )