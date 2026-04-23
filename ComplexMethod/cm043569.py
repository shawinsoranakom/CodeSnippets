def _handle_data_repr(obbject: OBBject) -> str:
            """Handle data representation for obbjects."""
            data_repr = ""
            if hasattr(obbject, "results") and obbject.results:
                data_schema = (
                    obbject.results[0].model_json_schema()
                    if obbject.results
                    and isinstance(obbject.results, list)
                    and hasattr(obbject.results[0], "model_json_schema")
                    else ""
                )
                if data_schema and "title" in data_schema:
                    data_repr = f"{data_schema['title']}"  # type: ignore
                if data_schema and "description" in data_schema:
                    data_repr += f" - {data_schema['description'].split('.')[0]}"  # type: ignore

            return data_repr