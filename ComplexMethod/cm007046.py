def fetch_content(self) -> list[Data]:
        try:
            # Only process domains if they're provided
            include_domains = None
            exclude_domains = None

            if self.include_domains:
                include_domains = [domain.strip() for domain in self.include_domains.split(",") if domain.strip()]

            if self.exclude_domains:
                exclude_domains = [domain.strip() for domain in self.exclude_domains.split(",") if domain.strip()]

            url = "https://api.tavily.com/search"
            headers = {
                "content-type": "application/json",
                "accept": "application/json",
            }

            payload = {
                "api_key": self.api_key,
                "query": self.query,
                "search_depth": self.search_depth,
                "topic": self.topic,
                "max_results": self.max_results,
                "include_images": self.include_images,
                "include_answer": self.include_answer,
                "include_raw_content": self.include_raw_content,
                "days": self.days,
                "time_range": self.time_range,
            }

            # Only add domains to payload if they exist and have values
            if include_domains:
                payload["include_domains"] = include_domains
            if exclude_domains:
                payload["exclude_domains"] = exclude_domains

            # Add conditional parameters only if they should be included
            if self.search_depth == "advanced" and self.chunks_per_source:
                payload["chunks_per_source"] = self.chunks_per_source

            if self.topic == "news" and self.days:
                payload["days"] = int(self.days)  # Ensure days is an integer

            # Add time_range if it's set
            if hasattr(self, "time_range") and self.time_range:
                payload["time_range"] = self.time_range

            # Add timeout handling
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload, headers=headers)

            response.raise_for_status()
            search_results = response.json()

            data_results = []

            if self.include_answer and search_results.get("answer"):
                data_results.append(Data(text=search_results["answer"]))

            for result in search_results.get("results", []):
                content = result.get("content", "")
                result_data = {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": content,
                    "score": result.get("score"),
                }
                if self.include_raw_content:
                    result_data["raw_content"] = result.get("raw_content")

                data_results.append(Data(text=content, data=result_data))

            if self.include_images and search_results.get("images"):
                data_results.append(Data(text="Images found", data={"images": search_results["images"]}))

        except httpx.TimeoutException:
            error_message = "Request timed out (90s). Please try again or adjust parameters."
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        except httpx.HTTPStatusError as exc:
            error_message = f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        except httpx.RequestError as exc:
            error_message = f"Request error occurred: {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        except ValueError as exc:
            error_message = f"Invalid response format: {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        else:
            self.status = data_results
            return data_results