def get_competitor_urls(url: str = None, description: str = None) -> list[str]:
            if not url and not description:
                raise ValueError("Please provide either a URL or a description.")

            if search_engine == "Perplexity AI - Sonar Pro":
                perplexity_url = "https://api.perplexity.ai/chat/completions"

                content = "Find me 3 competitor company URLs similar to the company with "
                if url and description:
                    content += f"URL: {url} and description: {description}"
                elif url:
                    content += f"URL: {url}"
                else:
                    content += f"description: {description}"
                content += ". ONLY RESPOND WITH THE URLS, NO OTHER TEXT."

                payload = {
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Be precise and only return 3 company URLs ONLY."
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.2,
                }

                headers = {
                    "Authorization": f"Bearer {st.session_state.perplexity_api_key}",
                    "Content-Type": "application/json"
                }

                try:
                    response = requests.post(perplexity_url, json=payload, headers=headers)
                    response.raise_for_status()
                    urls = response.json()['choices'][0]['message']['content'].strip().split('\n')
                    return [url.strip() for url in urls if url.strip()]
                except Exception as e:
                    st.error(f"Error fetching competitor URLs from Perplexity: {str(e)}")
                    return []

            else:  # Exa AI
                try:
                    # Use ExaTools agent to find competitor URLs
                    if url:
                        prompt = f"Find 3 competitor company URLs similar to: {url}. Return ONLY the URLs, one per line."
                    else:
                        prompt = f"Find 3 competitor company URLs matching this description: {description}. Return ONLY the URLs, one per line."

                    response: RunOutput = competitor_finder_agent.run(prompt)
                    # Extract URLs from the response
                    urls = [line.strip() for line in response.content.strip().split('\n') if line.strip() and line.strip().startswith('http')]
                    return urls[:3]  # Return up to 3 URLs
                except Exception as e:
                    st.error(f"Error fetching competitor URLs from Exa: {str(e)}")
                    return []