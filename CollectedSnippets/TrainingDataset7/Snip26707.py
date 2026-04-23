def csp_report_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        csp_reports.append(data)
    return HttpResponse(status=204)