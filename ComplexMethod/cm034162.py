def _validate_action_group_metadata(action, found_group_metadata, fq_group_name):
    valid_metadata = {
        'extend_group': {
            'types': (list, str,),
            'errortype': 'list',
        },
    }

    metadata_warnings = []

    validate = C.VALIDATE_ACTION_GROUP_METADATA
    metadata_only = isinstance(action, dict) and 'metadata' in action and len(action) == 1

    if validate and not metadata_only:
        found_keys = ', '.join(sorted(list(action)))
        metadata_warnings.append("The only expected key is metadata, but got keys: {keys}".format(keys=found_keys))
    elif validate:
        if found_group_metadata:
            metadata_warnings.append("The group contains multiple metadata entries.")
        if not isinstance(action['metadata'], dict):
            metadata_warnings.append("The metadata is not a dictionary. Got {metadata}".format(metadata=action['metadata']))
        else:
            unexpected_keys = set(action['metadata'].keys()) - set(valid_metadata.keys())
            if unexpected_keys:
                metadata_warnings.append("The metadata contains unexpected keys: {0}".format(', '.join(unexpected_keys)))
            unexpected_types = []
            for field, requirement in valid_metadata.items():
                if field not in action['metadata']:
                    continue
                value = action['metadata'][field]
                if not isinstance(value, requirement['types']):
                    unexpected_types.append("%s is %s (expected type %s)" % (field, value, requirement['errortype']))
            if unexpected_types:
                metadata_warnings.append("The metadata contains unexpected key types: {0}".format(', '.join(unexpected_types)))
    if metadata_warnings:
        metadata_warnings.insert(0, "Invalid metadata was found for action_group {0} while loading module_defaults.".format(fq_group_name))
        display.warning(" ".join(metadata_warnings))