def async_payment_middleware(get_response):
    async def middleware(request):
        response = await get_response(request)
        response.status_code = 402
        return response

    return middleware