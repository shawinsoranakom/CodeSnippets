def book(request, book_id):
    b = Book.objects.get(id=book_id)
    return HttpResponse(b.title)