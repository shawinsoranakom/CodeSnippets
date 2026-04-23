async def async_method_nested(self, request):
        try:
            await self._async_method_inner(request)
        except Exception:
            exc_info = sys.exc_info()
            send_log(request, exc_info)
            return technical_500_response(request, *exc_info)