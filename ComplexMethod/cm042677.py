def run(self, args: list[str], opts: argparse.Namespace) -> None:
        # load contracts
        assert self.settings is not None
        contracts = build_component_list(
            self.settings.get_component_priority_dict_with_base("SPIDER_CONTRACTS")
        )
        conman = ContractsManager(load_object(c) for c in contracts)
        runner = TextTestRunner(verbosity=2 if opts.verbose else 1)
        result = TextTestResult(runner.stream, runner.descriptions, runner.verbosity)

        # contract requests
        contract_reqs = defaultdict(list)

        assert self.crawler_process
        spider_loader = self.crawler_process.spider_loader

        async def start(self: Spider) -> AsyncIterator[Any]:
            for request in conman.from_spider(self, result):
                yield request

        with set_environ(SCRAPY_CHECK="true"):
            for spidername in args or spider_loader.list():
                spidercls = spider_loader.load(spidername)
                spidercls.start = start  # type: ignore[method-assign]

                tested_methods = conman.tested_methods_from_spidercls(spidercls)
                if opts.list:
                    for method in tested_methods:
                        contract_reqs[spidercls.name].append(method)
                elif tested_methods:
                    self.crawler_process.crawl(spidercls)

            # start checks
            if opts.list:
                print(
                    "\n".join(
                        f"{spider}\n"
                        + "\n".join(f"  * {method}" for method in sorted(methods))
                        for spider, methods in sorted(contract_reqs.items())
                        if methods or opts.verbose
                    )
                )
            else:
                start_time = time.monotonic()
                self.crawler_process.start()
                stop = time.monotonic()

                result.printErrors()
                result.printSummary(start_time, stop)
                self.exitcode = int(not result.wasSuccessful())