async def select(self, subject: str = None, predicate: str = None, object_: str = None) -> List[SPO]:
        """Retrieve triples from the directed graph repository based on specified criteria.

        Args:
            subject (str, optional): The subject of the triple to filter by.
            predicate (str, optional): The predicate describing the relationship to filter by.
            object_ (str, optional): The object of the triple to filter by.

        Returns:
            List[SPO]: A list of SPO objects representing the selected triples.

        Example:
            selected_triples = await my_di_graph_repo.select(subject="Node1", predicate="connects_to")
            # Retrieves directed relationships where Node1 is the subject and the predicate is 'connects_to'.
        """
        result = []
        for s, o, p in self._repo.edges(data="predicate"):
            if subject and subject != s:
                continue
            if predicate and predicate != p:
                continue
            if object_ and object_ != o:
                continue
            result.append(SPO(subject=s, predicate=p, object_=o))
        return result