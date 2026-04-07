def get_person(request, pk):
    person = get_object_or_404(Person, pk=pk)
    return HttpResponse(person.name)