from pyparsing import empty
from typing import List, Union
import disnake, wavelink, datetime

assets = {
    "equalizer": "https://i.imgur.com/v6GglMP.gif",
    "flat-equalizer": "https://i.imgur.com/q1UzHI9.png",
    "music_placeholder": "https://i.imgur.com/i6siEpW.png",
    "image_placeholder": "https://i.imgur.com/LZUXbqF.jpg",
    "spacer": "https://i.imgur.com/dWTmPGX.png",
    "pause": "https://i.imgur.com/oo5r8ys.png",
}


def NowPlayingEmbed(
    *,
    track: wavelink.YouTubeTrack = None,
    requester: disnake.Member = None,
    requested: datetime.datetime = None,
    thumbnail: str = None,
    bot: disnake.Member = None,
    pause: bool = False,
) -> disnake.Embed:
    if not track:
        embed = disnake.Embed(
            title="\n[No music playing or queued]",
            timestamp=datetime.datetime.now(),
            url="https://www.youtube.com/watch?v=OUx6ZY60uiI",
        )
        embed.set_thumbnail(assets["music_placeholder"])
        embed.set_image(url=assets["flat-equalizer"])
        embed.set_footer(
            text=f"Requested by {bot.display_name}", icon_url=bot.display_avatar.url
        )

    else:
        embed = disnake.Embed(
            title=f"Now Playing: {track.title}",
            timestamp=requested,
            url=track.uri,
        )
        embed.set_thumbnail(thumbnail)
        image = "pause" if pause else "equalizer"
        embed.set_image(url=assets[image])
        embed.set_footer(
            text=f"Requested by {requester.display_name}",
            icon_url=requester.display_avatar.url,
        )
    return embed


def TrackEnqueuedEmbed(track: wavelink.YouTubeTrack) -> disnake.Embed:
    title = f"Track Enqueued: {track.title}"
    embed = disnake.Embed(title=title, url=track.uri)
    # embed.set_thumbnail(track.thumbnail)
    embed.set_image(assets["spacer"])
    embed.set_footer(
        text=f"Requested by {track.requester.display_name}",
        icon_url=track.requester.display_avatar.url,
    )
    return embed


def QueueItem(
    *,
    count: int,
    requester: disnake.Member = None,
    requested: datetime.datetime = None,
    thumbnail: str = None,
    track: wavelink.YouTubeTrack,
) -> disnake.Embed:
    embed = disnake.Embed(title=f"{count}. {track.title}", timestamp=track.requested)
    if count == 1:
        embed.set_thumbnail(track.thumbnail)
    embed.set_image(assets["spacer"])
    embed.set_footer(
        text=track.requester.display_name, icon_url=track.requester.display_avatar.url
    )
    return embed


def EmptyQueueItem(*, count: int, bot: disnake.Member) -> disnake.Embed:
    embed = disnake.Embed(title=f"{count}. No songs in queue.")
    embed.set_thumbnail(assets["image_placeholder"])
    embed.set_image(assets["spacer"])
    embed.set_footer(text=bot.display_name, icon_url=bot.display_avatar.url)
    return embed
