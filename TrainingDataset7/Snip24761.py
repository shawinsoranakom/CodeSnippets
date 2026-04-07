def in_transaction(request):
    return HttpResponse(str(connection.in_atomic_block))