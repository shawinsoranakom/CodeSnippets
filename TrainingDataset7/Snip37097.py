def json_response_view(request):
    return JsonResponse(
        {
            "a": [1, 2, 3],
            "foo": {"bar": "baz"},
            # Make sure datetime and Decimal objects would be serialized
            # properly
            "timestamp": datetime.datetime(2013, 5, 19, 20),
            "value": decimal.Decimal("3.14"),
        }
    )