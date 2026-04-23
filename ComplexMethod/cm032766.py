async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message):

        if len(message.content.split('> ')) == 1:
            await message.channel.send("Hi~ How can I help you? ")
        else:
            JSON_DATA['word'] = message.content.split('> ')[1]
            response = requests.post(URL, json=JSON_DATA)
            response_data = response.json().get('data', [])
            image_bool = False

            for i in response_data:
                if i['type'] == 1:
                    res = i['content']
                if i['type'] == 3:
                    image_bool = True
                    image_data = base64.b64decode(i['url'])
                    with open('tmp_image.png', 'wb') as file:
                        file.write(image_data)
                    image = discord.File('tmp_image.png')

            await message.channel.send(f"{message.author.mention}{res}")

            if image_bool:
                await message.channel.send(file=image)