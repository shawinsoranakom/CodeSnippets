def _paginate_url(
        self,
        url_suffix: str,
        limit: int | None = None,
        # Called with the next url to use to get the next page
        next_page_callback: Callable[[str], None] | None = None,
        force_offset_pagination: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """
        This will paginate through the top level query.
        """
        if not limit:
            limit = _DEFAULT_PAGINATION_LIMIT

        url_suffix = update_param_in_path(url_suffix, "limit", str(limit))

        while url_suffix:
            logging.debug(f"Making confluence call to {url_suffix}")
            try:
                raw_response = self.get(
                    path=url_suffix,
                    advanced_mode=True,
                    params={
                        "body-format": "atlas_doc_format",
                        "expand": "body.atlas_doc_format",
                    },
                )
            except Exception as e:
                logging.exception(f"Error in confluence call to {url_suffix}")
                raise e

            try:
                raw_response.raise_for_status()
            except Exception as e:
                logging.warning(f"Error in confluence call to {url_suffix}")

                # If the problematic expansion is in the url, replace it
                # with the replacement expansion and try again
                # If that fails, raise the error
                if _PROBLEMATIC_EXPANSIONS in url_suffix:
                    logging.warning(
                        f"Replacing {_PROBLEMATIC_EXPANSIONS} with {_REPLACEMENT_EXPANSIONS}"
                        " and trying again."
                    )
                    url_suffix = url_suffix.replace(
                        _PROBLEMATIC_EXPANSIONS,
                        _REPLACEMENT_EXPANSIONS,
                    )
                    continue

                # If we fail due to a 500, try one by one.
                # NOTE: this iterative approach only works for server, since cloud uses cursor-based
                # pagination
                if raw_response.status_code == 500 and not self._is_cloud:
                    initial_start = get_start_param_from_url(url_suffix)
                    if initial_start is None:
                        # can't handle this if we don't have offset-based pagination
                        raise

                    # this will just yield the successful items from the batch
                    new_url_suffix = yield from self._try_one_by_one_for_paginated_url(
                        url_suffix,
                        initial_start=initial_start,
                        limit=limit,
                    )

                    # this means we ran into an empty page
                    if new_url_suffix is None:
                        if next_page_callback:
                            next_page_callback("")
                        break

                    url_suffix = new_url_suffix
                    continue

                else:
                    logging.exception(
                        f"Error in confluence call to {url_suffix} \n"
                        f"Raw Response Text: {raw_response.text} \n"
                        f"Full Response: {raw_response.__dict__} \n"
                        f"Error: {e} \n"
                    )
                    raise

            try:
                next_response = raw_response.json()
            except Exception as e:
                logging.exception(
                    f"Failed to parse response as JSON. Response: {raw_response.__dict__}"
                )
                raise e

            # Yield the results individually.
            results = cast(list[dict[str, Any]], next_response.get("results", []))

            # Note 1:
            # Make sure we don't update the start by more than the amount
            # of results we were able to retrieve. The Confluence API has a
            # weird behavior where if you pass in a limit that is too large for
            # the configured server, it will artificially limit the amount of
            # results returned BUT will not apply this to the start parameter.
            # This will cause us to miss results.
            #
            # Note 2:
            # We specifically perform manual yielding (i.e., `for x in xs: yield x`) as opposed to using a `yield from xs`
            # because we *have to call the `next_page_callback`* prior to yielding the last element!
            #
            # If we did:
            #
            # ```py
            # yield from results
            # if next_page_callback:
            #   next_page_callback(url_suffix)
            # ```
            #
            # then the logic would fail since the iterator would finish (and the calling scope would exit out of its driving
            # loop) prior to the callback being called.

            old_url_suffix = url_suffix
            updated_start = get_start_param_from_url(old_url_suffix)
            url_suffix = cast(str, next_response.get("_links", {}).get("next", ""))
            for i, result in enumerate(results):
                updated_start += 1
                if url_suffix and next_page_callback and i == len(results) - 1:
                    # update the url if we're on the last result in the page
                    if not self._is_cloud:
                        # If confluence claims there are more results, we update the start param
                        # based on how many results were returned and try again.
                        url_suffix = update_param_in_path(
                            url_suffix, "start", str(updated_start)
                        )
                    # notify the caller of the new url
                    next_page_callback(url_suffix)

                elif force_offset_pagination and i == len(results) - 1:
                    url_suffix = update_param_in_path(
                        old_url_suffix, "start", str(updated_start)
                    )

                yield result

            # we've observed that Confluence sometimes returns a next link despite giving
            # 0 results. This is a bug with Confluence, so we need to check for it and
            # stop paginating.
            if url_suffix and not results:
                logging.info(
                    f"No results found for call '{old_url_suffix}' despite next link "
                    "being present. Stopping pagination."
                )
                break