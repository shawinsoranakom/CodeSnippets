def parse_invalid_json(self, body: str) -> dict:
        """This is a quick fix to unblock cdk users setting cors policy for rest apis.
        CDK creates a MOCK OPTIONS route with in valid json. `{statusCode: 200}`
        Aws probably has a custom token parser. We can implement one
        at some point if we have user requests for it"""

        def convert_null_value(value) -> str:
            if (value := value.strip()) in ("null", ""):
                return '""'
            return value

        try:
            statuscode = ""
            matched = re.match(r"^\s*{(.+)}\s*$", body).group(1)
            pairs = [m.strip() for m in matched.split(",")]
            # TODO this is not right, but nested object would otherwise break the parsing
            key_values = [s.split(":", maxsplit=1) for s in pairs if s]
            for key_value in key_values:
                assert len(key_value) == 2
                key, value = [convert_null_value(el) for el in key_value]

                if key in ("statusCode", "'statusCode'", '"statusCode"'):
                    statuscode = int(value)
                    continue

                assert (leading_key_char := key[0]) not in "[{"
                if leading_key_char in "'\"":
                    assert len(key) >= 2
                    assert key[-1] == leading_key_char

                if (leading_value_char := value[0]) in "[{'\"":
                    assert len(value) >= 2
                    if leading_value_char == "{":
                        # TODO reparse objects
                        assert value[-1] == "}"
                    elif leading_value_char == "[":
                        # TODO validate arrays
                        assert value[-1] == "]"
                    else:
                        assert value[-1] == leading_value_char

            return {"statusCode": statuscode}

        except Exception as e:
            LOG.debug(
                "Error Parsing an invalid json, %s", e, exc_info=LOG.isEnabledFor(logging.DEBUG)
            )
            return {"statusCode": ""}