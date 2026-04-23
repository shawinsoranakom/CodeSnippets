def create_api_key(
        self,
        context: RequestContext,
        name: String = None,
        description: String = None,
        enabled: Boolean = None,
        generate_distinct_id: Boolean = None,
        value: String = None,
        stage_keys: ListOfStageKeys = None,
        customer_id: String = None,
        tags: MapOfStringToString = None,
        **kwargs,
    ) -> ApiKey:
        if name and len(name) > 1024:
            raise BadRequestException("Invalid API Key name, can be at most 1024 characters.")
        if value:
            if len(value) > 128:
                raise BadRequestException("API Key value exceeds maximum size of 128 characters")
            elif len(value) < 20:
                raise BadRequestException("API Key value should be at least 20 characters")
        if description and len(description) > 125000:
            raise BadRequestException("Invalid API Key description specified.")
        api_key = call_moto(context)
        if name == "":
            api_key.pop("name", None)
        #  transform array of stage keys [{'restApiId': '0iscapk09u', 'stageName': 'dev'}] into
        #  array of strings ['0iscapk09u/dev']
        stage_keys = api_key.get("stageKeys", [])
        api_key["stageKeys"] = [f"{sk['restApiId']}/{sk['stageName']}" for sk in stage_keys]

        return api_key