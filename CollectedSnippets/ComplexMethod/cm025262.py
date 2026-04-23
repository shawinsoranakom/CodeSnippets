async def update_data(self) -> XboxData:
        """Fetch presence data."""

        me = await self.client.people.get_friend_by_xuid(self.client.xuid)
        friends = await self.client.people.get_friends_own()

        presence_data = {self.client.xuid: me.people[0]}
        presence_data.update(
            {
                friend.xuid: friend
                for friend in friends.people
                if friend.xuid in self.friend_subentries()
            }
        )

        # retrieve title details
        for person in presence_data.values():
            if presence_detail := next(
                (
                    d
                    for d in person.presence_details or []
                    if d.state == "Active" and d.title_id and d.is_game and d.is_primary
                ),
                None,
            ):
                if (
                    person.xuid in self.title_data
                    and presence_detail.title_id
                    == self.title_data[person.xuid].title_id
                ):
                    continue
                try:
                    title = await self.client.titlehub.get_title_info(
                        presence_detail.title_id
                    )
                except HTTPStatusError as e:
                    if e.response.status_code == HTTPStatus.NOT_FOUND:
                        continue
                    raise
                self.title_data[person.xuid] = title.titles[0]
            else:
                self.title_data.pop(person.xuid, None)
            person.last_seen_date_time_utc = self.last_seen_timestamp(person)
        return XboxData(presence_data, self.title_data)