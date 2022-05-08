from . import utils
from typing import Union
import disnake, wavelink, datetime
from pydoc import describe

assets = {
    "equalizer": "https://i.imgur.com/v6GglMP.gif",
    "flat-equalizer": "https://i.imgur.com/q1UzHI9.png",
    "thumbnail": "https://i.imgur.com/LZUXbqF.jpg",
}


def NowPlayingEmbed(
    *, track: wavelink.YouTubeTrack = None, bot: disnake.Member = None
) -> disnake.Embed:
    if not track:
        embed = disnake.Embed(
            title="\n[No music playing or queued]",
            timestamp=datetime.datetime.now(),
            url="https://www.youtube.com/watch?v=OUx6ZY60uiI",
        )
        embed.set_thumbnail(assets["thumbnail"])
        embed.set_image(url=assets["flat-equalizer"])
        embed.set_footer(
            text=f"Requested by {bot.display_name}", icon_url=bot.display_avatar.url
        )

    else:
        embed = disnake.Embed(
            title=f"Now Playing: {track.title}",
            timestamp=track.requested,
            url=track.uri,
        )
        embed.set_thumbnail(track.thumbnail)
        embed.set_image(url=assets["equalizer"])
        embed.set_footer(
            text=f"Requested by {track.requester.display_name}",
            icon_url=track.requester.display_avatar.url,
        )
    return embed


def TrackEnqueuedEmbed(
    track: wavelink.YouTubeTrack, author: Union[disnake.User, disnake.Member]
) -> disnake.Embed:
    title = f"Track Enqueued: {track.title}"
    embed = disnake.Embed(title=title, url=track.uri)
    embed.set_thumbnail(track.thumbnail)
    return embed


class QueueView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
