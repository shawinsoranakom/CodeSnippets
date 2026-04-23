def __getattr__(self, name: str) -> Any:
        if "_attributes" in self.__dict__ and name in self.__dict__["_attributes"]:
            # It is a dict of attributes that are not inputs or outputs all the raw data it should have the loop input.
            return self.__dict__["_attributes"][name]
        if "_inputs" in self.__dict__ and name in self.__dict__["_inputs"]:
            return self.__dict__["_inputs"][name].value
        if "_outputs_map" in self.__dict__ and name in self.__dict__["_outputs_map"]:
            return self.__dict__["_outputs_map"][name]
        if name in BACKWARDS_COMPATIBLE_ATTRIBUTES:
            return self.__dict__[f"_{name}"]
        if name.startswith("_") and name[1:] in BACKWARDS_COMPATIBLE_ATTRIBUTES:
            return self.__dict__[name]
        if name == "graph":
            # If it got up to here it means it was going to raise
            session_id = self._session_id if hasattr(self, "_session_id") else None
            user_id = self._user_id if hasattr(self, "_user_id") else None
            flow_name = self._flow_name if hasattr(self, "_flow_name") else None
            flow_id = self._flow_id if hasattr(self, "_flow_id") else None
            return PlaceholderGraph(
                flow_id=flow_id, user_id=str(user_id), session_id=session_id, context={}, flow_name=flow_name
            )
        msg = f"Attribute {name} not found in {self.__class__.__name__}"
        raise AttributeError(msg)