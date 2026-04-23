async def aseed_urls(
        self,
        domain_or_domains: Union[str, List[str]],
        config: Optional[SeedingConfig] = None,
        **kwargs
    ) -> Union[List[str], Dict[str, List[Union[str, Dict[str, Any]]]]]:
        """
        Discovers, filters, and optionally validates URLs for a given domain(s)
        using sitemaps and Common Crawl archives.

        Args:
            domain_or_domains: A single domain string (e.g., "iana.org") or a list of domains.
            config: A SeedingConfig object to control the seeding process.
                    Parameters passed directly via kwargs will override those in 'config'.
            **kwargs: Additional parameters (e.g., `source`, `live_check`, `extract_head`,
                      `pattern`, `concurrency`, `hits_per_sec`, `force_refresh`, `verbose`)
                      that will be used to construct or update the SeedingConfig.

        Returns:
            If `extract_head` is False:
                - For a single domain: `List[str]` of discovered URLs.
                - For multiple domains: `Dict[str, List[str]]` mapping each domain to its URLs.
            If `extract_head` is True:
                - For a single domain: `List[Dict[str, Any]]` where each dict contains 'url'
                  and 'head_data' (parsed <head> metadata).
                - For multiple domains: `Dict[str, List[Dict[str, Any]]]` mapping each domain
                  to a list of URL data dictionaries.

        Raises:
            ValueError: If `domain_or_domains` is not a string or a list of strings.
            Exception: Any underlying exceptions from AsyncUrlSeeder or network operations.

        Example:
            >>> # Discover URLs from sitemap with live check for 'example.com'
            >>> result = await crawler.aseed_urls("example.com", source="sitemap", live_check=True, hits_per_sec=10)

            >>> # Discover URLs from Common Crawl, extract head data for 'example.com' and 'python.org'
            >>> multi_domain_result = await crawler.aseed_urls(
            >>>     ["example.com", "python.org"],
            >>>     source="cc", extract_head=True, concurrency=200, hits_per_sec=50
            >>> )
        """
        # Initialize AsyncUrlSeeder here if it hasn't been already
        if not self.url_seeder:
            # Pass the crawler's base_directory for seeder's cache management
            # Pass the crawler's logger for consistent logging
            self.url_seeder = AsyncUrlSeeder(
                base_directory=self.crawl4ai_folder,
                logger=self.logger
            )                    

        # Merge config object with direct kwargs, giving kwargs precedence
        seeding_config = config.clone(**kwargs) if config else SeedingConfig.from_kwargs(kwargs)

        # Ensure base_directory is set for the seeder's cache
        seeding_config.base_directory = seeding_config.base_directory or self.crawl4ai_folder        
        # Ensure the seeder uses the crawler's logger (if not already set)
        if not self.url_seeder.logger:
            self.url_seeder.logger = self.logger

        # Pass verbose setting if explicitly provided in SeedingConfig or kwargs
        if seeding_config.verbose is not None:
            self.url_seeder.logger.verbose = seeding_config.verbose
        else: # Default to crawler's verbose setting
            self.url_seeder.logger.verbose = self.logger.verbose


        if isinstance(domain_or_domains, str):
            self.logger.info(
                message="Starting URL seeding for domain: {domain}",
                tag="SEED",
                params={"domain": domain_or_domains}
            )
            return await self.url_seeder.urls(
                domain_or_domains,
                seeding_config
            )
        elif isinstance(domain_or_domains, (list, tuple)):
            self.logger.info(
                message="Starting URL seeding for {count} domains",
                tag="SEED",
                params={"count": len(domain_or_domains)}
            )
            # AsyncUrlSeeder.many_urls directly accepts a list of domains and individual params.
            return await self.url_seeder.many_urls(
                domain_or_domains,
                seeding_config
            )
        else:
            raise ValueError("`domain_or_domains` must be a string or a list of strings.")