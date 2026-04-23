def _get_contracts(self, date_start=None, date_end=None, use_latest_version=True, domain=None):
        """
        Retrieve the contracts for employees within a specified date range and based
        on specified criteria, such as domain filtering and version selection.

        This method is used to collect and organize employee contracts based on their
        versions, date ranges, and other specified options. The resulting contracts are
        grouped by employee, and their selection logic depends on whether the latest
        version should be used or not. It supports flexibility in contract retrieval by
        allowing optional filters for date range and domain.

        Args:
            date_start (Optional[datetime.date]): The start date to filter the contracts
                by. If provided, only contract versions <= this date are considered
                based on the selection logic.
            date_end (Optional[datetime.date]): The end date to filter the contracts by.
                Only contract versions within the range will be retrieved. Defaults to
                None if not specified.
            domain (Optional[dict]): A dictionary representing additional filters or
                constraints to apply to the contract versions retrieved. Defaults to
                None.
            use_latest_version (bool): Indicates whether to retrieve the version
            effective at the end of the contract (or before the date_end) for each employee (True) or
            at the start of the contract (before the date_start) (False). Defaults to True.

        Returns:
            collections.defaultdict: A dictionary mapping each employee's identifier
            (employee.id) to a set of their corresponding contracts. Each set contains
            version records retrieved and filtered based on the specified criteria.
        """
        contract_versions_by_employee = self._get_contract_versions(date_start, date_end, domain)
        contracts_by_employee = defaultdict(lambda: self.env["hr.version"])
        for employee_id in contract_versions_by_employee:
            for contract_versions in contract_versions_by_employee[employee_id].values():
                effective_date = date_end if use_latest_version else date_start
                if use_latest_version:
                    if effective_date:
                        correct_versions = contract_versions.filtered(lambda v: v.date_version <= effective_date)
                        contracts_by_employee[employee_id] |= correct_versions[-1] if correct_versions else contract_versions[0]
                    else:
                        contracts_by_employee[employee_id] |= contract_versions[-1] if use_latest_version else contract_versions[0]
        return contracts_by_employee