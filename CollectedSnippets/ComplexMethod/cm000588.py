async def search_people(self, query: SearchPeopleRequest) -> List[Contact]:
        """Search for people in Apollo"""
        response = await self.requests.post(
            f"{self.API_URL}/mixed_people/search",
            headers=self._get_headers(),
            json=query.model_dump(exclude={"max_results"}),
        )
        data = response.json()
        parsed_response = SearchPeopleResponse(**data)
        if parsed_response.pagination.total_entries == 0:
            return []

        people = parsed_response.people

        # handle pagination
        if (
            query.max_results is not None
            and query.max_results < parsed_response.pagination.total_entries
            and len(people) < query.max_results
        ):
            while (
                len(people) < query.max_results
                and query.page < parsed_response.pagination.total_pages
                and len(parsed_response.people) > 0
            ):
                query.page += 1
                response = await self.requests.post(
                    f"{self.API_URL}/mixed_people/search",
                    headers=self._get_headers(),
                    json=query.model_dump(exclude={"max_results"}),
                )
                data = response.json()
                parsed_response = SearchPeopleResponse(**data)
                people.extend(parsed_response.people[: query.max_results - len(people)])

        logger.info(f"Found {len(people)} people")
        return people[: query.max_results] if query.max_results else people