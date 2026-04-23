def get_worst_toy():
    toy, _ = Toy.objects.get_or_create(name="worst")
    return toy