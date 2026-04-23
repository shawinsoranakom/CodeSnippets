def on_response(self, response):
        if response.data.geo:
            self._writer.write(
                {
                    "type": "geo-tagged",
                    "tweet": response.data.data,
                    "includes": {
                        key: [value.data for value in val_l]
                        for (key, val_l) in response.includes.items()
                    },
                },
            )
        elif (
            len(response.includes["users"]) > 0
            and response.includes["users"][0].location
        ):
            self._writer.write(
                {
                    "type": "user-location",
                    "tweet": response.data.data,
                    "includes": {
                        key: [value.data for value in val_l]
                        for (key, val_l) in response.includes.items()
                    },
                },
            )
        else:
            self._writer.write(
                {
                    "type": "no-location",
                    "tweet": response.data.data,
                    "includes": {
                        key: [value.data for value in val_l]
                        for (key, val_l) in response.includes.items()
                    },
                },
            )