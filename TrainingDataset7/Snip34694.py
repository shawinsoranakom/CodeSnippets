def raw_post_view(request):
    """A view which expects raw XML to be posted and returns content extracted
    from the XML"""
    if request.method == "POST":
        root = parseString(request.body)
        first_book = root.firstChild.firstChild
        title, author = [n.firstChild.nodeValue for n in first_book.childNodes]
        t = Template("{{ title }} - {{ author }}", name="Book template")
        c = Context({"title": title, "author": author})
    else:
        t = Template("GET request.", name="Book GET template")
        c = Context()

    return HttpResponse(t.render(c))