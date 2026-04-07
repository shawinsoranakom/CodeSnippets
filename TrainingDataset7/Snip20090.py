def post_form_view(request):
    """Return a POST form (without a token)."""
    return HttpResponse(content="""
<html>
<body><h1>\u00a1Unicode!<form method="post"><input type="text"></form></body>
</html>
""")