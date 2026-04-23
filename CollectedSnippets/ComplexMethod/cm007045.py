def fetch_content(self) -> list[Data]:
        """Fetches and processes extracted content into a list of Data objects."""
        try:
            # Split URLs by comma and clean them
            urls = [url.strip() for url in (self.urls or "").split(",") if url.strip()]
            if not urls:
                error_message = "No valid URLs provided"
                logger.error(error_message)
                return [Data(text=error_message, data={"error": error_message})]

            url = "https://api.tavily.com/extract"
            headers = {
                "content-type": "application/json",
                "accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            payload = {
                "urls": urls,
                "extract_depth": self.extract_depth,
                "include_images": self.include_images,
            }

            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

        except httpx.TimeoutException as exc:
            error_message = f"Request timed out (90s): {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        except httpx.HTTPStatusError as exc:
            error_message = f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        except (ValueError, KeyError, AttributeError, httpx.RequestError) as exc:
            error_message = f"Data processing error: {exc}"
            logger.error(error_message)
            return [Data(text=error_message, data={"error": error_message})]
        else:
            extract_results = response.json()
            data_results = []

            # Process successful extractions
            for result in extract_results.get("results", []):
                raw_content = result.get("raw_content", "")
                images = result.get("images", [])
                result_data = {"url": result.get("url"), "raw_content": raw_content, "images": images}
                data_results.append(Data(text=raw_content, data=result_data))

            # Process failed extractions
            if extract_results.get("failed_results"):
                data_results.append(
                    Data(
                        text="Failed extractions",
                        data={"failed_results": extract_results["failed_results"]},
                    )
                )

            self.status = data_results
            return data_results