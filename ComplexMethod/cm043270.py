def _process_element(
        self,
        url: str,
        element: lhtml.HtmlElement,
        media: Dict[str, List],
        internal_links_dict: Dict[str, Any],
        external_links_dict: Dict[str, Any],
        page_context: dict = None,
        **kwargs,
    ) -> bool:
        base_domain = kwargs.get("base_domain", get_base_domain(url))
        exclude_domains = set(kwargs.get("exclude_domains", []))

        # Process links
        try:
            base_element = element.xpath("//head/base[@href]")
            if base_element:
                base_href = base_element[0].get("href", "").strip()
                if base_href:
                    url = base_href
        except Exception as e:
            self._log("error", f"Error extracting base URL: {str(e)}", "SCRAPE")
            pass

        for link in element.xpath(".//a[@href]"):
            href = link.get("href", "").strip()
            if not href:
                continue

            try:
                normalized_href = normalize_url(
                    href, url,
                    preserve_https=kwargs.get('preserve_https_for_internal_links', False),
                    original_scheme=kwargs.get('original_scheme')
                )
                link_data = {
                    "href": normalized_href,
                    "text": link.text_content().strip(),
                    "title": link.get("title", "").strip(),
                    "base_domain": base_domain,
                }

                # Add intrinsic scoring if enabled
                if kwargs.get("score_links", False) and page_context is not None:
                    try:
                        intrinsic_score = calculate_link_intrinsic_score(
                            link_text=link_data["text"],
                            url=normalized_href,
                            title_attr=link_data["title"],
                            class_attr=link.get("class", ""),
                            rel_attr=link.get("rel", ""),
                            page_context=page_context
                        )
                        link_data["intrinsic_score"] = intrinsic_score
                    except Exception:
                        # Fail gracefully - assign default score
                        link_data["intrinsic_score"] = 0
                else:
                    # No scoring enabled - assign infinity (all links equal priority)
                    link_data["intrinsic_score"] = 0

                is_external = is_external_url(normalized_href, base_domain)
                if is_external:
                    link_base_domain = get_base_domain(normalized_href)
                    link_data["base_domain"] = link_base_domain
                    if (
                        kwargs.get("exclude_external_links", False)
                        or link_base_domain in exclude_domains
                    ):
                        link.getparent().remove(link)
                        continue

                    if normalized_href not in external_links_dict:
                        external_links_dict[normalized_href] = link_data
                else:
                    if normalized_href not in internal_links_dict:
                        internal_links_dict[normalized_href] = link_data

            except Exception as e:
                self._log("error", f"Error processing link: {str(e)}", "SCRAPE")
                continue

        # Process images
        images = element.xpath(".//img")
        total_images = len(images)

        for idx, img in enumerate(images):
            src = img.get("src") or ""
            img_domain = get_base_domain(src)

            # Decide if we need to exclude this image
            # 1) If its domain is in exclude_domains, remove.
            # 2) Or if exclude_external_images=True and it's an external domain, remove.
            if (img_domain in exclude_domains) or (
                kwargs.get("exclude_external_images", False)
                and is_external_url(src, base_domain)
            ):
                parent = img.getparent()
                if parent is not None:
                    parent.remove(img)
                continue

            # Otherwise, process the image as usual.
            try:
                processed_images = self.process_image(
                    img, url, idx, total_images, **kwargs
                )
                if processed_images:
                    media["images"].extend(processed_images)
            except Exception as e:
                self._log("error", f"Error processing image: {str(e)}", "SCRAPE")

        # Process videos and audios
        for media_type in ["video", "audio"]:
            for elem in element.xpath(f".//{media_type}"):
                media_info = {
                    "src": elem.get("src"),
                    "alt": elem.get("alt"),
                    "type": media_type,
                    "description": self.find_closest_parent_with_useful_text(
                        elem, **kwargs
                    ),
                }
                media[f"{media_type}s"].append(media_info)

                # Process source tags within media elements
                for source in elem.xpath(".//source"):
                    if src := source.get("src"):
                        media[f"{media_type}s"].append({**media_info, "src": src})

        # Clean up unwanted elements
        if kwargs.get("remove_forms", False):
            for form in element.xpath(".//form"):
                form.getparent().remove(form)

        if excluded_tags := kwargs.get("excluded_tags", []):
            for tag in excluded_tags:
                for elem in element.xpath(f".//{tag}"):
                    elem.getparent().remove(elem)

        if excluded_selector := kwargs.get("excluded_selector", ""):
            try:
                for elem in element.cssselect(excluded_selector):
                    elem.getparent().remove(elem)
            except Exception:
                pass  # Invalid selector

        return True