def get_account_settings(self, context: RequestContext, **kwargs) -> GetAccountSettingsResponse:
        state = lambda_stores[context.account_id][context.region]

        fn_count = 0
        code_size_sum = 0
        reserved_concurrency_sum = 0
        for fn in state.functions.values():
            fn_count += 1
            for fn_version in fn.versions.values():
                # Image-based Lambdas do not have a code attribute and count against the ECR quotas instead
                if fn_version.config.package_type == PackageType.Zip:
                    code_size_sum += fn_version.config.code.code_size
            if fn.reserved_concurrent_executions is not None:
                reserved_concurrency_sum += fn.reserved_concurrent_executions
            for c in fn.provisioned_concurrency_configs.values():
                reserved_concurrency_sum += c.provisioned_concurrent_executions
        for layer in state.layers.values():
            for layer_version in layer.layer_versions.values():
                code_size_sum += layer_version.code.code_size
        return GetAccountSettingsResponse(
            AccountLimit=AccountLimit(
                TotalCodeSize=config.LAMBDA_LIMITS_TOTAL_CODE_SIZE,
                CodeSizeZipped=config.LAMBDA_LIMITS_CODE_SIZE_ZIPPED,
                CodeSizeUnzipped=config.LAMBDA_LIMITS_CODE_SIZE_UNZIPPED,
                ConcurrentExecutions=config.LAMBDA_LIMITS_CONCURRENT_EXECUTIONS,
                UnreservedConcurrentExecutions=config.LAMBDA_LIMITS_CONCURRENT_EXECUTIONS
                - reserved_concurrency_sum,
            ),
            AccountUsage=AccountUsage(
                TotalCodeSize=code_size_sum,
                FunctionCount=fn_count,
            ),
        )