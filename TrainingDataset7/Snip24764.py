def not_in_transaction_using_text(request):
    return HttpResponse(str(connection.in_atomic_block))