def gen_image_banana(chatbot, history, text_prompt, image_base64_list=None, resolution="1K", aspectRatio="1:1", model="nano-banana"):
    """
    Generate image using Nano-banana API (optimized DALL-E format API)

    Args:
        text_prompt: Text description for image generation
        image_base64_list: List of base64 encoded images or URLs (optional, for image-to-image)
        resolution: Image size, one of: "1K", "2K", "4K" (default: "1K")
        aspectRatio: Aspect ratio like "1:1", "16:9", "3:4", "4:3", "9:16", "2:3", "3:2", "4:5", "5:4", "21:9" (default: "1:1")
        model: Model name, "nano-banana" or "nano-banana-hd" for 4K quality (default: "nano-banana")

    Returns:
        tuple: (image_url, local_file_path)
    """


    proxies = get_conf('proxies')

    # Get API configuration
    if not get_conf('REROUTE_ALL_TO_ONE_API'):
        api_key = get_conf('GEMINI_API_KEY')
        # Default to a generic endpoint if not using ONE_API
        base_url = get_conf('GEMINI_BASE_URL') if get_conf('GEMINI_BASE_URL') else "https://api.example.com"
        if base_url.endswith('/v1'):
            base_url = base_url[:-3]
        url = base_url + "/v1/images/generations"
        download_image_proxies = proxies
    else:
        url = get_conf('ONE_API_URL')
        api_key = get_conf('ONE_API_KEY')
        if api_key == '$API_KEY':
            api_key = get_conf('API_KEY')
        download_image_proxies = proxies
        proxies = None

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Make API request

    try:
        payload = {
            "model": "google/gemini-3-pro-image-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text_prompt
                        },
                    ]
                }
            ],
            "modalities": ["image", "text"],
            "image_config": {
                "aspect_ratio": aspectRatio,
                "image_size": resolution
            }
        }

        for image_base64 in image_base64_list:
            # {
            #     "type": "image_url",
            #     "image_url": {
            #         "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
            #     }
            # }
            # img = f"data:image/jpeg;base64,{base64_image}"

            payload["messages"][0]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            })


        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        image_url = None
        generated_content = ""
        if result.get("choices"):
            message = result["choices"][0]["message"]
            if message.get("images"):
                generated_content = message.get('reasoning', "") + message.get('content', "")
                for image in message["images"]:
                    image_url = image["image_url"]["url"]
                    print(f"Generated image: {image_url[:50]}...")


        if response.status_code != 200:
            yield from update_ui_latest_msg(lastmsg=f"Generate Failed\n\n{generated_content}\n\nStatus Code: {response.status_code}", chatbot=chatbot, history=history, delay=0)
            return

        if image_url is None:
            raise RuntimeError("No image URL found in the response.")

        logger.info(f'Generated image.')
        yield from update_ui_latest_msg(lastmsg=f"Downloading image", chatbot=chatbot, history=history, delay=0)

        if ';base64,' in image_url:
            base64_string = image_url.split('base64,')[-1]
            image_data = base64.b64decode(base64_string)
            file_path = f'{get_log_folder()}/image_gen/'
            os.makedirs(file_path, exist_ok=True)
            file_name = 'Image' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.png'
            fp = file_path+file_name
            with open(fp, 'wb+') as f: f.write(image_data)
        else:
            raise ValueError("Invalid image URL format.")

        return image_url, fp

    except Exception as e:
        yield from update_ui_latest_msg(lastmsg=f"Generate failed, please try again later.", chatbot=chatbot, history=history, delay=0)
        raise RuntimeError(f"Failed to generate image, please try again later: {str(e)}")