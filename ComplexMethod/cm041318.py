def get_aws_service_status(
        self, service_name: str, operation_name: str | None = None
    ) -> AwsServicesSupportStatus | None:
        if not self.services_in_latest:
            return None
        if service_name not in self.services_in_latest:
            return AwsServicesSupportInLatest.NOT_SUPPORTED
        if self.current_emulator_type not in self.services_in_latest[service_name]:
            return AwsServicesSupportInLatest.SUPPORTED_WITH_LICENSE_UPGRADE
        if not operation_name:
            return AwsServicesSupportInLatest.SUPPORTED
        if operation_name in self.services_in_latest[service_name][self.current_emulator_type]:
            return AwsServiceOperationsSupportInLatest.SUPPORTED
        for emulator_type in self.services_in_latest[service_name]:
            if emulator_type is self.current_emulator_type:
                continue
            if operation_name in self.services_in_latest[service_name][emulator_type]:
                return AwsServiceOperationsSupportInLatest.SUPPORTED_WITH_LICENSE_UPGRADE
        return AwsServiceOperationsSupportInLatest.NOT_SUPPORTED