def from_name(func_name: StatesFunctionName, argument_list: ArgumentList) -> StatesFunction:
        match func_name.function_type:
            # Array.
            case StatesFunctionNameType.Array:
                return array.Array(argument_list=argument_list)
            case StatesFunctionNameType.ArrayPartition:
                return array_partition.ArrayPartition(argument_list=argument_list)
            case StatesFunctionNameType.ArrayContains:
                return array_contains.ArrayContains(argument_list=argument_list)
            case StatesFunctionNameType.ArrayRange:
                return array_range.ArrayRange(argument_list=argument_list)
            case StatesFunctionNameType.ArrayGetItem:
                return array_get_item.ArrayGetItem(argument_list=argument_list)
            case StatesFunctionNameType.ArrayLength:
                return array_length.ArrayLength(argument_list=argument_list)
            case StatesFunctionNameType.ArrayUnique:
                return array_unique.ArrayUnique(argument_list=argument_list)

            # JSON Manipulation
            case StatesFunctionNameType.JsonToString:
                return json_to_string.JsonToString(argument_list=argument_list)
            case StatesFunctionNameType.StringToJson:
                return string_to_json.StringToJson(argument_list=argument_list)
            case StatesFunctionNameType.JsonMerge:
                return json_merge.JsonMerge(argument_list=argument_list)

            # Unique Id Generation.
            case StatesFunctionNameType.UUID:
                return uuid.UUID(argument_list=argument_list)

            # String Operations.
            case StatesFunctionNameType.StringSplit:
                return string_split.StringSplit(argument_list=argument_list)

            # Hash Calculations.
            case StatesFunctionNameType.Hash:
                return hash_func.HashFunc(argument_list=argument_list)

            # Encoding and Decoding.
            case StatesFunctionNameType.Base64Encode:
                return base_64_encode.Base64Encode(argument_list=argument_list)
            case StatesFunctionNameType.Base64Decode:
                return base_64_decode.Base64Decode(argument_list=argument_list)

            # Math Operations.
            case StatesFunctionNameType.MathRandom:
                return math_random.MathRandom(argument_list=argument_list)
            case StatesFunctionNameType.MathAdd:
                return math_add.MathAdd(argument_list=argument_list)

            # Generic.
            case StatesFunctionNameType.Format:
                return string_format.StringFormat(argument_list=argument_list)

            # Unsupported.
            case unsupported:
                raise NotImplementedError(unsupported)