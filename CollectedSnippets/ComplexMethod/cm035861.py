def get_usernames(self, spreadsheet_id: str, range_name: str = 'A:A') -> List[str]:
        """Get list of usernames from specified Google Sheet.
        Uses cached data if available and less than 15 seconds old.
        Args:
            spreadsheet_id: The ID of the Google Sheet
            range_name: The A1 notation of the range to fetch
        Returns:
            List of usernames from the sheet
        """
        if not self.client:
            logger.error('Google Sheets client not initialized')
            return []

        # Try to get from cache first
        cached_usernames = self._get_from_cache(spreadsheet_id, range_name)
        if cached_usernames is not None:
            return cached_usernames

        try:
            logger.info(
                f'Fetching usernames from sheet {spreadsheet_id}, range {range_name}'
            )
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1  # Get first worksheet
            values = worksheet.get(range_name)

            usernames = [
                str(cell[0]).strip() for cell in values if cell and cell[0].strip()
            ]
            logger.info(
                f'Successfully fetched {len(usernames)} usernames from Google Sheet'
            )

            # Update cache with new data
            self._update_cache(spreadsheet_id, range_name, usernames)
            return usernames

        except gspread.exceptions.APIError:
            logger.exception(f'Error accessing Google Sheet {spreadsheet_id}')
            return []
        except Exception:
            logger.exception(
                f'Unexpected error accessing Google Sheet {spreadsheet_id}'
            )
            return []