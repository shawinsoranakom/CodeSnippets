def merge_response(value: ServiceResponse) -> list[Any]:
        """Merge action responses into single list.

        Checks that the input is a correct service response:
        {
            "entity_id": {str: dict[str, Any]},
        }
        If response is a single list, it will extend the list with the items
            and add the entity_id and value_key to each dictionary for reference.
        If response is a dictionary or multiple lists,
            it will append the dictionary/lists to the list
            and add the entity_id to each dictionary for reference.
        """
        if not isinstance(value, dict):
            raise TypeError("Response is not a dictionary")
        if not value:
            return []

        is_single_list = False
        response_items: list = []
        input_service_response = deepcopy(value)
        for entity_id, entity_response in input_service_response.items():  # pylint: disable=too-many-nested-blocks
            if not isinstance(entity_response, dict):
                raise TypeError("Response is not a dictionary")
            for value_key, type_response in entity_response.items():
                if len(entity_response) == 1 and isinstance(type_response, list):
                    is_single_list = True
                    for dict_in_list in type_response:
                        if isinstance(dict_in_list, dict):
                            if ATTR_ENTITY_ID in dict_in_list:
                                raise ValueError(
                                    f"Response dictionary already contains key '{ATTR_ENTITY_ID}'"
                                )
                            dict_in_list[ATTR_ENTITY_ID] = entity_id
                            dict_in_list["value_key"] = value_key
                    response_items.extend(type_response)
                else:
                    break

            if not is_single_list:
                _response = entity_response.copy()
                if ATTR_ENTITY_ID in _response:
                    raise ValueError(
                        f"Response dictionary already contains key '{ATTR_ENTITY_ID}'"
                    )
                _response[ATTR_ENTITY_ID] = entity_id
                response_items.append(_response)

        return response_items