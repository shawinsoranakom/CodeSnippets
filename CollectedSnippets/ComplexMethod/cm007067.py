def json_query(self) -> Data:
        import json

        try:
            import jq
        except ImportError:
            msg = "jq is required for JQ Expression. Install with: pip install jq"
            raise ImportError(msg) from None

        if not self.query or not self.query.strip():
            msg = "JSON Query is required and cannot be blank."
            raise ValueError(msg)
        raw_data = self.get_data_dict()
        try:
            input_str = json.dumps(raw_data)
            repaired = repair_json(input_str)
            data_json = json.loads(repaired)
            jq_input = data_json["data"] if isinstance(data_json, dict) and "data" in data_json else data_json
            results = jq.compile(self.query).input(jq_input).all()
            if not results:
                msg = "No result from JSON query."
                raise ValueError(msg)
            result = results[0] if len(results) == 1 else results
            if result is None or result == "None":
                msg = "JSON query returned null/None. Check if the path exists in your data."
                raise ValueError(msg)
            if isinstance(result, dict):
                return Data(data=result)
            return Data(data={"result": result})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"JSON Query failed: {e}")
            msg = f"JSON Query error: {e}"
            raise ValueError(msg) from e