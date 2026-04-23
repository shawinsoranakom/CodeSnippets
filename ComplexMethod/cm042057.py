async def _get_class_use_cases(self, ns_class_name: str) -> str:
        """
        Asynchronously assembles the context about the use case information of the namespace-prefixed SPO object.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which to retrieve use case information.

        Returns:
            str: A string containing the assembled context about the use case information.
        """
        block = ""
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_USE_CASE)
        for i, r in enumerate(rows):
            detail = ReverseUseCaseDetails.model_validate_json(r.object_)
            block += f"\n### {i + 1}. {detail.description}"
            for j, use_case in enumerate(detail.use_cases):
                block += f"\n#### {i + 1}.{j + 1}. {use_case.description}\n"
                block += "\n##### Inputs\n" + "\n".join([f"- {s}" for s in use_case.inputs])
                block += "\n##### Outputs\n" + "\n".join([f"- {s}" for s in use_case.outputs])
                block += "\n##### Actors\n" + "\n".join([f"- {s}" for s in use_case.actors])
                block += "\n##### Steps\n" + "\n".join([f"- {s}" for s in use_case.steps])
            block += "\n#### Use Case Relationship\n" + "\n".join([f"- {s}" for s in detail.relationship])
        return block + "\n"