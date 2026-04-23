def __init__(self, request):
        self.domain = self.name = request.get_host()