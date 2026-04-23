def list_grants(
        self, context: RequestContext, request: ListGrantsRequest
    ) -> ListGrantsResponse:
        if not request.get("KeyId"):
            raise ValidationError("Required input parameter KeyId not specified")
        key_account_id, key_region_name, _ = self._parse_key_id(request["KeyId"], context)
        # KeyId can potentially hold one of multiple different types of key identifiers. Here we find a key no
        # matter which type of id is used.
        key = self._get_kms_key(
            key_account_id, key_region_name, request.get("KeyId"), any_key_state_allowed=True
        )
        key_id = key.metadata.get("KeyId")

        store = self._get_store(context.account_id, context.region)
        grant_id = request.get("GrantId")
        if grant_id:
            if grant_id not in store.grants:
                raise InvalidGrantIdException()
            return ListGrantsResponse(Grants=[store.grants[grant_id].metadata])

        matching_grants = []
        grantee_principal = request.get("GranteePrincipal")
        for grant in store.grants.values():
            # KeyId is a mandatory field of ListGrants request, so is going to be present.
            _, _, grant_key_id = parse_key_arn(grant.metadata["KeyArn"])
            if grant_key_id != key_id:
                continue
            # GranteePrincipal is a mandatory field for CreateGrant, should be in grants. But it is an optional field
            # for ListGrants, so might not be there.
            if grantee_principal and grant.metadata["GranteePrincipal"] != grantee_principal:
                continue
            matching_grants.append(grant.metadata)

        grants_list = PaginatedList(matching_grants)
        page, next_token = grants_list.get_page(
            lambda grant_data: grant_data.get("GrantId"),
            next_token=request.get("Marker"),
            page_size=request.get("Limit", 50),
        )
        kwargs = {"NextMarker": next_token, "Truncated": True} if next_token else {}

        return ListGrantsResponse(Grants=page, **kwargs)