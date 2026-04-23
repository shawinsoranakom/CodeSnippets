def choice_default():
    return ChoiceOptionModel.objects.get_or_create(name="default")[0].pk