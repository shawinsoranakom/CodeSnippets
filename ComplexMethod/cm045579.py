def _parse_html(
        self, url: str, rank_start: int = 0, first: int = 1
    ) -> Tuple[List[SearchItem], str]:
        """
        Parse Bing search result HTML to extract search results and the next page URL.

        Returns:
            tuple: (List of SearchItem objects, next page URL or None)
        """
        try:
            res = self.session.get(url=url)
            res.encoding = "utf-8"
            root = BeautifulSoup(res.text, "lxml")

            list_data = []
            ol_results = root.find("ol", id="b_results")
            if not ol_results:
                return [], None

            for li in ol_results.find_all("li", class_="b_algo"):
                title = ""
                url = ""
                abstract = ""
                try:
                    h2 = li.find("h2")
                    if h2:
                        title = h2.text.strip()
                        url = h2.a["href"].strip()

                    p = li.find("p")
                    if p:
                        abstract = p.text.strip()

                    if ABSTRACT_MAX_LENGTH and len(abstract) > ABSTRACT_MAX_LENGTH:
                        abstract = abstract[:ABSTRACT_MAX_LENGTH]

                    rank_start += 1

                    # Create a SearchItem object
                    list_data.append(
                        SearchItem(
                            title=title or f"Bing Result {rank_start}",
                            url=url,
                            description=abstract,
                        )
                    )
                except Exception:
                    continue

            next_btn = root.find("a", title="Next page")
            if not next_btn:
                return list_data, None

            next_url = BING_HOST_URL + next_btn["href"]
            return list_data, next_url
        except Exception as e:
            logger.warning(f"Error parsing HTML: {e}")
            return [], None