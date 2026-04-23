def update(self) -> None:
        """Get the latest data and update the states."""

        try:
            response = requests.get(_RESOURCE, params=self.params, timeout=5)
            data = response.content.decode("utf-8")
            data_dict = xmltodict.parse(data)[ZESTIMATE]
            error_code = int(data_dict["message"]["code"])
            if error_code != 0:
                _LOGGER.error("The API returned: %s", data_dict["message"]["text"])
                return
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from %s", _RESOURCE)
            return
        data = data_dict["response"][NAME]
        details = {}
        if "amount" in data and data["amount"] is not None:
            details[ATTR_AMOUNT] = data["amount"]["#text"]
            details[ATTR_CURRENCY] = data["amount"]["@currency"]
        if "last-updated" in data and data["last-updated"] is not None:
            details[ATTR_LAST_UPDATED] = data["last-updated"]
        if "valueChange" in data and data["valueChange"] is not None:
            details[ATTR_CHANGE] = int(data["valueChange"]["#text"])
        if "valuationRange" in data and data["valuationRange"] is not None:
            details[ATTR_VAL_HI] = int(data["valuationRange"]["high"]["#text"])
            details[ATTR_VAL_LOW] = int(data["valuationRange"]["low"]["#text"])
        self.address = data_dict["response"]["address"]["street"]
        self.data = details
        if self.data is not None:
            self._state = self.data[ATTR_AMOUNT]
        else:
            self._state = None
            _LOGGER.error("Unable to parase Zestimate data from response")