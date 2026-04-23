def _apply_global_transform(
        self,
        global_transform: GlobalTransform,
        template: dict,
        parameters: dict[str, EngineParameter],
    ) -> dict:
        transform_name = global_transform.name
        if transform_name == EXTENSIONS_TRANSFORM:
            resources = template["Resources"]
            mappings = template.get("Mappings", {})
            conditions = template.get("Conditions", {})

            resolve_context = ResolveRefsRecursivelyContext(
                self._change_set.account_id,
                self._change_set.region_name,
                self._change_set.stack.stack_name,
                resources,
                mappings,
                conditions,
                parameters=engine_parameters_to_stack_parameters(parameters),
            )
            transformed_template = apply_language_extensions_transform(template, resolve_context)
        elif transform_name == SERVERLESS_TRANSFORM:
            # serverless transform just requires the key/value pairs
            serverless_parameters = {}
            for name, param in parameters.items():
                serverless_parameters[name] = param.get("resolved_value") or engine_parameter_value(
                    param
                )
            transformed_template = self._apply_global_serverless_transformation(
                region_name=self._change_set.region_name,
                template=template,
                parameters=serverless_parameters,
            )
        elif transform_name == SECRETSMANAGER_TRANSFORM:
            # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/transform-aws-secretsmanager.html
            LOG.warning("%s is not yet supported. Ignoring.", SECRETSMANAGER_TRANSFORM)
            transformed_template = template
        elif transform_name == INCLUDE_TRANSFORM:
            transformed_template = self._compute_include_transform(
                parameters=global_transform.parameters,
                fragment=template,
            )
        else:
            transformed_template = self._invoke_macro(
                name=global_transform.name,
                parameters=global_transform.parameters
                if not is_nothing(global_transform.parameters)
                else {},
                fragment=template,
                allow_string=False,
            )
        return transformed_template