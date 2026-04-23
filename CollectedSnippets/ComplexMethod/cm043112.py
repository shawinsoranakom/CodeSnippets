async def stream_request(client: httpx.AsyncClient, endpoint: str, payload: Dict[str, Any], title: str):
    """Handles streaming POST requests."""
    console.rule(f"[bold magenta]{title}[/]", style="magenta")
    print_payload(payload)
    console.print(
        f"Sending POST stream request to {client.base_url}{endpoint}...")
    all_results = []
    initial_status_code = None  # Store initial status code

    try:
        start_time = time.time()
        async with client.stream("POST", endpoint, json=payload) as response:
            initial_status_code = response.status_code  # Capture initial status
            duration = time.time() - start_time  # Time to first byte potentially
            console.print(
                f"Initial Response Status: [bold {'green' if response.is_success else 'red'}]{initial_status_code}[/] (first byte ~{duration:.2f}s)")
            response.raise_for_status()  # Raise exception for bad *initial* status codes

            console.print("[magenta]--- Streaming Results ---[/]")
            completed = False
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("status") == "completed":
                            completed = True
                            console.print(
                                "[bold green]--- Stream Completed ---[/]")
                            break
                        elif data.get("url"):  # Looks like a result dictionary
                            all_results.append(data)
                            # Display summary info as it arrives
                            success_icon = "[green]✔[/]" if data.get(
                                'success') else "[red]✘[/]"
                            url = data.get('url', 'N/A')
                            # Display status code FROM THE RESULT DATA if available
                            result_status = data.get('status_code', 'N/A')
                            console.print(
                                f"  {success_icon} Received: [link={url}]{url}[/link] (Status: {result_status})")
                            if not data.get('success') and data.get('error_message'):
                                console.print(
                                    f"    [red]Error: {data['error_message']}[/]")
                        else:
                            console.print(
                                f"  [yellow]Stream meta-data:[/yellow] {data}")
                    except json.JSONDecodeError:
                        console.print(
                            f"  [red]Stream decode error for line:[/red] {line}")
            if not completed:
                console.print(
                    "[bold yellow]Warning: Stream ended without 'completed' marker.[/]")

    except httpx.HTTPStatusError as e:
        # Use the captured initial status code if available, otherwise from the exception
        status = initial_status_code if initial_status_code is not None else e.response.status_code
        console.print(f"[bold red]HTTP Error (Initial Request):[/]")
        console.print(f"Status: {status}")
        try:
            console.print(Panel(Syntax(json.dumps(
                e.response.json(), indent=2), "json", theme="default"), title="Error Response"))
        except json.JSONDecodeError:
            console.print(f"Response Body: {e.response.text}")
    except httpx.RequestError as e:
        console.print(f"[bold red]Request Error: {e}[/]")
    except Exception as e:
        console.print(f"[bold red]Unexpected Error during streaming: {e}[/]")
        # Print stack trace for unexpected errors
        console.print_exception(show_locals=False)

    # Call print_result_summary with the *collected* results AFTER the stream is done
    print_result_summary(all_results, title=f"{title} Collected Results")