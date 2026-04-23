def get(self, request):
        try:
            raise Exception
        except Exception:
            return technical_500_response(request, *sys.exc_info())