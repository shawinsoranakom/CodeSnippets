def thread_func():
            try:
                Car.objects.first()
            except DatabaseOperationForbidden as e:
                exceptions.append(e)