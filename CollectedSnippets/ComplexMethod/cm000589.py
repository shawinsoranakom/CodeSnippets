async def search_organizations(
        self, query: SearchOrganizationsRequest
    ) -> List[Organization]:
        """Search for organizations in Apollo"""
        response = await self.requests.post(
            f"{self.API_URL}/mixed_companies/search",
            headers=self._get_headers(),
            json=query.model_dump(exclude={"max_results"}),
        )
        data = response.json()
        parsed_response = SearchOrganizationsResponse(**data)
        if parsed_response.pagination.total_entries == 0:
            return []

        organizations = parsed_response.organizations

        # handle pagination
        if (
            query.max_results is not None
            and query.max_results < parsed_response.pagination.total_entries
            and len(organizations) < query.max_results
        ):
            while (
                len(organizations) < query.max_results
                and query.page < parsed_response.pagination.total_pages
                and len(parsed_response.organizations) > 0
            ):
                query.page += 1
                response = await self.requests.post(
                    f"{self.API_URL}/mixed_companies/search",
                    headers=self._get_headers(),
                    json=query.model_dump(exclude={"max_results"}),
                )
                data = response.json()
                parsed_response = SearchOrganizationsResponse(**data)
                organizations.extend(
                    parsed_response.organizations[
                        : query.max_results - len(organizations)
                    ]
                )

        logger.info(f"Found {len(organizations)} organizations")
        return (
            organizations[: query.max_results] if query.max_results else organizations
        )