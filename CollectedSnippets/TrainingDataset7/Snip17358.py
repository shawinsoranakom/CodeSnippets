def post_view(request):
            try:
                loop.call_soon_threadsafe(view_started_event.set)
                time.sleep(0.1)
                # Do something to read request.body after pause
                outcome.append({"request_body": request.body})
                return HttpResponse("ok")
            except Exception as e:
                outcome.append({"exception": e})
            finally:
                loop.call_soon_threadsafe(view_finished_event.set)