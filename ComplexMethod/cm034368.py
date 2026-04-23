def form_urlencoded(body):
    """ Convert data into a form-urlencoded string """
    if isinstance(body, str):
        return body

    if isinstance(body, (Mapping, Sequence)):
        result = []
        # Turn a list of lists into a list of tuples that urlencode accepts
        for key, values in kv_list(body):
            if isinstance(values, str) or not isinstance(values, (Mapping, Sequence)):
                values = [values]
            for value in values:
                if value is not None:
                    result.append((to_text(key), to_text(value)))
        return urlencode(result, doseq=True)

    return body