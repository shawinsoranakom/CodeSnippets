def __init__(
        self,
        account_id: str,
        region_name: str,
        metadata: CreateChangeSetInput | None = None,
        template: StackTemplate | None = None,
        template_body: str | None = None,
    ):
        self.account_id = account_id
        self.region_name = region_name

        if template is None:
            template = {}

        self.resolved_outputs = []  # TODO
        self.resolved_parameters: dict[str, StackParameter] = {}
        self.resolved_conditions: dict[str, bool] = {}

        self.metadata = metadata or {}
        self.template = template or {}
        self.template_body = template_body
        self._template_raw = clone_safe(self.template)
        self.template_original = clone_safe(self.template)
        # initialize resources
        for resource_id, resource in self.template_resources.items():
            # HACK: if the resource is a Fn::ForEach intrinsic call from the LanguageExtensions transform, then it is not a dictionary but a list
            if resource_id.startswith("Fn::ForEach"):
                # we are operating on an untransformed template, so ignore for now
                continue
            resource["LogicalResourceId"] = self.template_original["Resources"][resource_id][
                "LogicalResourceId"
            ] = resource.get("LogicalResourceId") or resource_id
        # initialize stack template attributes
        stack_id = self.metadata.get("StackId") or arns.cloudformation_stack_arn(
            self.stack_name,
            stack_id=StackIdentifier(
                account_id=account_id, region=region_name, stack_name=metadata.get("StackName")
            ).generate(tags=metadata.get("tags")),
            account_id=account_id,
            region_name=region_name,
        )
        self.template["StackId"] = self.metadata["StackId"] = stack_id
        self.template["Parameters"] = self.template.get("Parameters") or {}
        self.template["Outputs"] = self.template.get("Outputs") or {}
        self.template["Conditions"] = self.template.get("Conditions") or {}
        # initialize metadata
        self.metadata["Parameters"] = self.metadata.get("Parameters") or []
        self.metadata["StackStatus"] = "CREATE_IN_PROGRESS"
        self.metadata["CreationTime"] = self.metadata.get("CreationTime") or timestamp_millis()
        self.metadata["LastUpdatedTime"] = self.metadata["CreationTime"]
        self.metadata.setdefault("Description", self.template.get("Description"))
        self.metadata.setdefault("RollbackConfiguration", {})
        self.metadata.setdefault("DisableRollback", False)
        self.metadata.setdefault("EnableTerminationProtection", False)
        # maps resource id to resource state
        self._resource_states = {}
        # list of stack events
        self.events = []
        # list of stack change sets
        self.change_sets = []