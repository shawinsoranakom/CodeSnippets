def model_view(request):
    people = Person.objects.all()
    return HttpResponse("\n".join(person.name for person in people))