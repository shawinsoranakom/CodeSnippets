def update(self):
        """Get the latest data from opendata.ch."""
        params = {}
        params["stopid"] = self.stop

        if self.route:
            params["routeid"] = self.route

        params["maxresults"] = 2
        params["format"] = "json"

        response = requests.get(_RESOURCE, params, timeout=10)

        if response.status_code != HTTPStatus.OK:
            self.info = [
                {ATTR_DUE_AT: "n/a", ATTR_ROUTE: self.route, ATTR_DUE_IN: "n/a"}
            ]
            return

        result = response.json()

        if str(result["errorcode"]) != "0":
            self.info = [
                {ATTR_DUE_AT: "n/a", ATTR_ROUTE: self.route, ATTR_DUE_IN: "n/a"}
            ]
            return

        self.info = []
        for item in result["results"]:
            due_at = item.get("departuredatetime")
            route = item.get("route")
            if due_at is not None and route is not None:
                bus_data = {
                    ATTR_DUE_AT: due_at,
                    ATTR_ROUTE: route,
                    ATTR_DUE_IN: due_in_minutes(due_at),
                }
                self.info.append(bus_data)

        if not self.info:
            self.info = [
                {ATTR_DUE_AT: "n/a", ATTR_ROUTE: self.route, ATTR_DUE_IN: "n/a"}
            ]