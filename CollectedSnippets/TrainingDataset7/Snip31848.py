def create_model_instance(request):
    person = Person(name="emily")
    person.save()
    return HttpResponse()