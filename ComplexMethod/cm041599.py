def map_to_notimplemented(row: RowEntry) -> bool:
    """
    Some simple heuristics to check the API responses and classify them into implemented/notimplemented

    Ideally they all should behave the same way when receiving requests for not yet implemented endpoints
    (501 error code and avoids relying on static "not yet implemented" error message strings)

    :param row: the RowEntry
    :return: True if we assume it is not implemented, False otherwise
    """
    if row["status_code"] in [STATUS_PARSING_ERROR]:
        # parsing issues are nearly always due to something not being implemented or activated
        return True
    if row["status_code"] in [STATUS_TIMEOUT_ERROR]:
        #  timeout issue, interpreted as implemented until there's a better heuristic
        return False
    if row["status_code"] == STATUS_CONNECTION_ERROR:
        return True
    if (
        row["service"] == "cloudfront"
        and row["status_code"] == 500
        and row.get("error_code") == "500"
        and row.get("error_message", "").lower() == "internal server error"
    ):
        return True
    if row["service"] == "dynamodb" and row.get("error_code") == "UnknownOperationException":
        return True
    if row["service"] == "lambda" and row["status_code"] == 404 and row.get("error_code") == "404":
        return True
    if (
        row["service"]
        in [
            "route53",
            "s3control",
        ]
        and row["status_code"] == 404
        and row.get("error_code") == "404"
        and row.get("error_message") is not None
        and "not found" == row.get("error_message", "").lower()
    ):
        return True
    if (
        row["service"] in ["xray", "batch", "glacier", "resource-groups", "apigateway"]
        and row["status_code"] == 404
        and row.get("error_message") is not None
        and "The requested URL was not found on the server" in row.get("error_message")
    ):
        return True
    if row["status_code"] == 501:
        return True
    if (
        row["status_code"] == 500
        and row.get("error_code") == "500"
        and not row.get("error_message")
    ):
        return True
    return False