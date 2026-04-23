def list_transcripts(self) -> list[Data]:
        aai.settings.api_key = self.api_key

        params = aai.ListTranscriptParameters()
        if self.limit:
            params.limit = self.limit
        if self.status_filter != "all":
            params.status = self.status_filter
        if self.created_on and self.created_on.text:
            params.created_on = self.created_on.text
        if self.throttled_only:
            params.throttled_only = True

        try:
            transcriber = aai.Transcriber()

            def convert_page_to_data_list(page):
                return [Data(**t.dict()) for t in page.transcripts]

            if self.limit == 0:
                # paginate over all pages
                params.limit = 100
                page = transcriber.list_transcripts(params)
                transcripts = convert_page_to_data_list(page)

                while page.page_details.before_id_of_prev_url is not None:
                    params.before_id = page.page_details.before_id_of_prev_url
                    page = transcriber.list_transcripts(params)
                    transcripts.extend(convert_page_to_data_list(page))
            else:
                # just one page
                page = transcriber.list_transcripts(params)
                transcripts = convert_page_to_data_list(page)

        except Exception as e:  # noqa: BLE001
            logger.debug("Error listing transcripts", exc_info=True)
            error_data = Data(data={"error": f"An error occurred: {e}"})
            self.status = [error_data]
            return [error_data]

        self.status = transcripts
        return transcripts