def return_json_response_latin1(request):
    return HttpResponse(
        b'{"a":"\xc5"}', content_type="application/json; charset=latin1"
    )