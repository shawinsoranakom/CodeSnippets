def _resolve_pseudo_parameter(self, pseudo_parameter_name: str) -> Any:
        match pseudo_parameter_name:
            case "AWS::Partition":
                return get_partition(self._change_set.region_name)
            case "AWS::AccountId":
                return self._change_set.stack.account_id
            case "AWS::Region":
                return self._change_set.stack.region_name
            case "AWS::StackName":
                return self._change_set.stack.stack_name
            case "AWS::StackId":
                return self._change_set.stack.stack_id
            case "AWS::URLSuffix":
                return _AWS_URL_SUFFIX
            case "AWS::NoValue":
                return None
            case _:
                raise RuntimeError(f"The use of '{pseudo_parameter_name}' is currently unsupported")