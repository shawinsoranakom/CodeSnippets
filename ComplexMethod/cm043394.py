def crawl(self, url: str, **kwargs) -> str:
        # Create md5 hash of the URL
        import hashlib

        url_hash = hashlib.md5(url.encode()).hexdigest()

        if self.use_cached_html:
            cache_file_path = os.path.join(
                os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()),
                ".crawl4ai",
                "cache",
                url_hash,
            )
            if os.path.exists(cache_file_path):
                with open(cache_file_path, "r") as f:
                    return sanitize_input_encode(f.read())

        try:
            self.driver = self.execute_hook("before_get_url", self.driver)
            if self.verbose:
                print(f"[LOG] 🕸️ Crawling {url} using LocalSeleniumCrawlerStrategy...")
            self.driver.get(url)  # <html><head></head><body></body></html>

            WebDriverWait(self.driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )

            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            self.driver = self.execute_hook("after_get_url", self.driver)
            html = sanitize_input_encode(
                self._ensure_page_load()
            )  # self.driver.page_source
            can_not_be_done_headless = (
                False  # Look at my creativity for naming variables
            )

            # TODO: Very ugly approach, but promise to change it!
            if (
                kwargs.get("bypass_headless", False)
                or html == "<html><head></head><body></body></html>"
            ):
                print(
                    "[LOG] 🙌 Page could not be loaded in headless mode. Trying non-headless mode..."
                )
                can_not_be_done_headless = True
                options = Options()
                options.headless = False
                # set window size very small
                options.add_argument("--window-size=5,5")
                driver = webdriver.Chrome(service=self.service, options=options)
                driver.get(url)
                self.driver = self.execute_hook("after_get_url", driver)
                html = sanitize_input_encode(driver.page_source)
                driver.quit()

            # Execute JS code if provided
            self.js_code = kwargs.get("js_code", self.js_code)
            if self.js_code and type(self.js_code) == str:
                self.driver.execute_script(self.js_code)
                # Optionally, wait for some condition after executing the JS code
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState")
                    == "complete"
                )
            elif self.js_code and type(self.js_code) == list:
                for js in self.js_code:
                    self.driver.execute_script(js)
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.execute_script(
                            "return document.readyState"
                        )
                        == "complete"
                    )

            # Optionally, wait for some condition after executing the JS code : Contributed by (https://github.com/jonymusky)
            wait_for = kwargs.get("wait_for", False)
            if wait_for:
                if callable(wait_for):
                    print("[LOG] 🔄 Waiting for condition...")
                    WebDriverWait(self.driver, 20).until(wait_for)
                else:
                    print("[LOG] 🔄 Waiting for condition...")
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                    )

            if not can_not_be_done_headless:
                html = sanitize_input_encode(self.driver.page_source)
            self.driver = self.execute_hook("before_return_html", self.driver, html)

            # Store in cache
            cache_file_path = os.path.join(
                os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()),
                ".crawl4ai",
                "cache",
                url_hash,
            )
            with open(cache_file_path, "w", encoding="utf-8") as f:
                f.write(html)

            if self.verbose:
                print(f"[LOG] ✅ Crawled {url} successfully!")

            return html
        except InvalidArgumentException as e:
            if not hasattr(e, "msg"):
                e.msg = sanitize_input_encode(str(e))
            raise InvalidArgumentException(f"Failed to crawl {url}: {e.msg}")
        except WebDriverException as e:
            # If e does nlt have msg attribute create it and set it to str(e)
            if not hasattr(e, "msg"):
                e.msg = sanitize_input_encode(str(e))
            raise WebDriverException(f"Failed to crawl {url}: {e.msg}")
        except Exception as e:
            if not hasattr(e, "msg"):
                e.msg = sanitize_input_encode(str(e))
            raise Exception(f"Failed to crawl {url}: {e.msg}")