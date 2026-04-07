async def view(request):
            nonlocal view_did_cancel
            view_started.set()
            try:
                await asyncio.sleep(0.1)
                return HttpResponse("Hello World!")
            except asyncio.CancelledError:
                # Set the flag.
                view_did_cancel = True
                raise