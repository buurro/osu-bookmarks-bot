import irc.bot
import irc.strings
import re
import requests
import json
import os

from irc.bot import ServerSpec
from dotenv import load_dotenv


load_dotenv()


class BookmarksBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, server):
        irc.bot.SingleServerIRCBot.__init__(self, [server], nickname, nickname)

    def __url_in_message(self, e):
        pattern = re.compile(r"(https://osu.ppy.sh/(?:b|beatmapsets|beatmaps)/\d+)")
        res = pattern.search(e.arguments[0])
        if res:
            return res.group(1)
        return None

    def bookmarkSong(self, c, e):
        api_baseurl = os.getenv("API_BASEURL")

        url = self.__url_in_message(e)
        if not url:
            return None

        nick = e.source.nick

        mutation = """
            mutation ($input: SongInput!){
                addSong (input: $input)  {
                    osuUserId,
                    bookmarksUrl,
                    beatmapset {
                        osuBeatmapsetId,
                        title,
                        artist,
                    }
                }
            }"""
        mutation_input = {"userName": nick, "mapUrl": url}
        query = {"query": mutation, "variables": {"input": mutation_input}}
        print(query)
        try:
            resp = requests.post(api_baseurl + "/graphql", json=query)
        except requests.exceptions.ConnectionError:
            c.privmsg(nick, "Something went wrong :(")
            return

        print(resp.status_code)
        print(resp.text)
        if resp.status_code != 200:
            c.privmsg(nick, "Something went wrong :(")
            return

        song = json.loads(resp.text)
        try:
            song = song["data"]["addSong"]
        except KeyError:
            c.privmsg(nick, "Something went wrong :(")
            return

        if not song:
            return

        bookmarks_url = api_baseurl + song["bookmarksUrl"]
        beatmap = song["beatmapset"]

        msg = "[https://osu.ppy.sh/beatmapsets/{} {} - {}] added to [{} your list]"
        msg = msg.format(
            beatmap["osuBeatmapsetId"],
            beatmap["artist"],
            beatmap["title"],
            bookmarks_url,
        )

        c.privmsg(nick, msg)

    def on_action(self, c, e):
        self.bookmarkSong(c, e)

    def on_privmsg(self, c, e):
        self.bookmarkSong(c, e)


def main():
    nickname = os.getenv("BOT_NICKNAME")
    server = "irc.ppy.sh"
    port = 6667

    spec = ServerSpec(server, port, os.getenv("BOT_PASSWORD"))
    bot = BookmarksBot(nickname, spec)
    bot.start()


if __name__ == "__main__":
    main()
