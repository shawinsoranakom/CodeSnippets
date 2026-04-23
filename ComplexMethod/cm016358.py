def _process_utilization_records(
        self,
        lines: list[str],
    ) -> tuple[list[UtilizationRecord], list[UtilizationRecord]]:
        results = [self._process_raw_record(line) for line in lines[1:]]
        valid_records = [
            record for record, valid in results if valid and record is not None
        ]
        invalid_records = [
            record for record, valid in results if not valid and record is not None
        ]
        return valid_records, invalid_records