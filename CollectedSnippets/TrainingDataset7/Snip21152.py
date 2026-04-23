def get_best_toy():
    toy, _ = Toy.objects.get_or_create(name="best")
    return toy