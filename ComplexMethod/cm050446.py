def pivot_measure_fields(pivot):
    measures = [
        measure if isinstance(measure, str)
        # "field" has been renamed to "name" and "name" to "fieldName"
        else measure["field"] if "field" in measure
        else measure["name"] if "name" in measure
        else measure["fieldName"]
        for measure in pivot["measures"]
        if "computedBy" not in measure
    ]
    return [
        measure
        for measure in measures
        if measure != "__count"
    ]