def return_undecodable_binary(request):
    return HttpResponse(
        b"%PDF-1.4\r\n%\x93\x8c\x8b\x9e ReportLab Generated PDF document "
        b"http://www.reportlab.com"
    )