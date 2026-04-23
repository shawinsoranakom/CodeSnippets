def astra_rest(self, args):
        headers = {"Accept": "application/json", "X-Cassandra-Token": f"{self.token}"}
        astra_url = f"{self.get_api_endpoint()}/api/rest/v2/keyspaces/{self.get_keyspace()}/{self.collection_name}/"
        where = {}

        for param in self.tools_params:
            field_name = param["field_name"] if param["field_name"] else param["name"]
            field_value = None

            if field_name in self.static_filters:
                field_value = self.static_filters[field_name]
            elif param["name"] in args:
                field_value = args[param["name"]]

            if field_value is None:
                continue

            if param["is_timestamp"] == True:  # noqa: E712
                try:
                    field_value = self.parse_timestamp(field_value)
                except ValueError as e:
                    msg = f"Error parsing timestamp: {e} - Use the prompt to specify the date in the correct format"
                    logger.error(msg)
                    raise ValueError(msg) from e

            if param["operator"] == "$exists":
                where[field_name] = {**where.get(field_name, {}), param["operator"]: True}
            elif param["operator"] in ["$in", "$nin", "$all"]:
                where[field_name] = {
                    **where.get(field_name, {}),
                    param["operator"]: field_value.split(",") if isinstance(field_value, str) else field_value,
                }
            else:
                where[field_name] = {**where.get(field_name, {}), param["operator"]: field_value}

        url = f"{astra_url}?page-size={self.number_of_results}"
        url += f"&where={json.dumps(where)}"

        if self.projection_fields != "*":
            url += f"&fields={urllib.parse.quote(self.projection_fields.replace(' ', ''))}"

        res = requests.request("GET", url=url, headers=headers, timeout=10)

        if int(res.status_code) >= HTTPStatus.BAD_REQUEST:
            msg = f"Error on Astra DB CQL Tool {self.tool_name} request: {res.text}"
            logger.error(msg)
            raise ValueError(msg)

        try:
            res_data = res.json()
            return res_data["data"]
        except ValueError:
            return res.status_code