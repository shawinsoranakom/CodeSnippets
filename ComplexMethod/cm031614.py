def tracer(frame, event, arg):
        if frame.f_code.co_filename != '<demo>':
            return tracer

        func_name = frame.f_code.co_name
        lineno = frame.f_lineno

        if event == 'line' and not tracing_active[0]:
            pending_line[0] = {'type': 'line', 'line': lineno}
            return tracer

        # Start tracing only once main() is called
        if event == 'call' and func_name == 'main':
            tracing_active[0] = True
            # Emit the buffered line event (the main() call line) at ts=0
            if pending_line[0]:
                pending_line[0]['ts'] = 0
                trace_events.append(pending_line[0])
                pending_line[0] = None
                timestamp[0] = timestamp_step

        # Skip events until we've entered main()
        if not tracing_active[0]:
            return tracer

        if event == 'call':
            trace_events.append({
                'type': 'call',
                'func': func_name,
                'line': lineno,
                'ts': timestamp[0],
            })
        elif event == 'line':
            trace_events.append({
                'type': 'line',
                'line': lineno,
                'ts': timestamp[0],
            })
        elif event == 'return':
            try:
                value = arg if arg is None else repr(arg)
            except Exception:
                value = '<unprintable>'
            trace_events.append({
                'type': 'return',
                'func': func_name,
                'ts': timestamp[0],
                'value': value,
            })

            if func_name == 'main':
                tracing_active[0] = False

        timestamp[0] += timestamp_step
        return tracer