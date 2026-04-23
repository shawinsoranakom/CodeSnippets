def scrape_articles(
    website_urls: list[str],
    refresh_interval: int = 600,
) -> Generator[dict[str, str | dict], None, None]:
    indexed_articles: set[str] = set()
    expand_articles: list[str] = []

    logging.info(f"Starting webscraper with number of urls: {len(website_urls)}")

    while True:
        for website in website_urls:
            logging.info(f"Extracting articles from: {website}")
            try:
                article_fetcher = NewspaperListArticles()
                page_article_urls = article_fetcher.list_articles(website)
            except ArticleBinaryDataException as e:
                warnings.warn(f"cannot fetch articles for {website}, {e}")
                continue
            else:
                logging.info(f"{website} found {len(page_article_urls)} articles.")

                expand_articles.extend(page_article_urls)

        logging.info(f"Total number of articles: {len(expand_articles)}")

        expand_articles = [i for i in expand_articles if i not in indexed_articles]

        article_ls: list = list(
            NewsPlease.from_urls(expand_articles, request_args={"timeout": 60}).values()
        )  # key: url, value: article. May have None entries

        articles: list[NewsArticle] = [
            article.get_serializable_dict() for article in article_ls if article
        ]

        logging.info(f"Number of fetched articles: {len(articles)}")

        for article in articles:
            url = article["url"]

            if url in indexed_articles:
                continue

            article = _locate_set_text(article)

            clean_article: NewsArticle | BasicNewsArticle = _clean_article_metadata(
                article
            )

            text = clean_article.pop("text", url)

            if text is None:
                continue

            metadata = clean_article

            indexed_articles.add(url)
            yield {"url": url, "text": text, "metadata": dict(metadata)}

        time.sleep(refresh_interval)