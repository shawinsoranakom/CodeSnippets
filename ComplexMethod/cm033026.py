def _list_records(
        self,
        sheet_id: str,
        next_token: str | None = None,
        max_results: int = 100,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        List records from a specific sheet with pagination.

        Args:
            sheet_id: The sheet ID
            next_token: Token for pagination
            max_results: Maximum number of results per page

        Returns:
            Tuple of (records list, next_token or None if no more)
        """
        headers = notable_models.ListRecordsHeaders()
        headers.x_acs_dingtalk_access_token = self._access_token

        request = notable_models.ListRecordsRequest(
            operator_id=self.operator_id,
            max_results=max_results,
            next_token=next_token or "",
        )

        try:
            response = self.client.list_records_with_options(
                self.table_id,
                sheet_id,
                request,
                headers,
                util_models.RuntimeOptions(),
            )

            records = []
            new_next_token = None

            if response.body:
                if response.body.records:
                    for record in response.body.records:
                        records.append(
                            {
                                "id": record.id,
                                "fields": record.fields,
                            }
                        )
                if response.body.next_token:
                    new_next_token = response.body.next_token

            return records, new_next_token

        except Exception as e:
            if not UtilClient.empty(getattr(e, "code", None)) and not UtilClient.empty(getattr(e, "message", None)):
                logger.error(f"[DingTalk AITable]: API error - code: {e.code}, message: {e.message}")
            raise