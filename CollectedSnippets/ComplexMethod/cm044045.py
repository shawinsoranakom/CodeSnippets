async def fetch_month(m: int) -> list[dict]:
                    """Fetch bulletins for a single month."""
                    url = f"{PUBLICATION_URL}?date={year}-{m:02d}"
                    bulletins = []

                    try:
                        resp = await session.get(url)
                        if resp.status != 200:
                            return []
                        html = await resp.text()
                    except Exception:
                        return []

                    pattern = (
                        r'href="(/sites/default/release-files/[^"]+\.pdf)"[^>]*>.*?'
                        r'<time datetime="(\d{4}-\d{2}-\d{2})T'
                    )
                    matches = re.findall(pattern, html, re.DOTALL)

                    for pdf_path, date_str in matches:
                        # Skip the "latest release" which appears on every page
                        if pdf_path == "/sites/default/release-files/795708/wwcb.pdf":
                            continue

                        # Parse the date
                        try:
                            dt = datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            continue

                        # Only include if it matches the requested year/month
                        if dt.year != year:
                            continue
                        if month is not None and dt.month != m:
                            continue

                        # Calculate week of month (1-5)
                        week_of_month = (dt.day - 1) // 7 + 1

                        # Filter by week if specified
                        if week is not None and week_of_month != week:
                            continue

                        # Extract filename from path
                        filename = pdf_path.split("/")[-1]

                        # Create human-readable label
                        label = f"Weekly Weather Bulletin - {dt.strftime('%Y-%m-%d')}"

                        bulletins.append(
                            {
                                "label": label,
                                "date": dt,
                                "year": dt.year,
                                "month": dt.month,
                                "day": dt.day,
                                "week_of_month": week_of_month,
                                "pdf_url": f"{BASE_URL}{pdf_path}",
                                "filename": filename,
                            }
                        )

                    return bulletins