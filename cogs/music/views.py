from typing import List, Union
import discord, wavelink, datetime

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
    track: wavelink.Playable = None,
    requester: discord.Member = None,
    requested: datetime.datetime = None,
    thumbnail: str = None
) -> discord.Embed:
    embed = discord.Embed(
        title=f"Now Playing: {track.title}",
        timestamp=requested,
        url=track.uri,
    )
    # embed.set_thumbnail(url=thumbnail)
    image = assets["music_placeholder"] if track.artwork is None else track.artwork
    embed.set_image(url=image)
    embed.set_footer(
        text=f"Requested by {requester.display_name}",
        icon_url=requester.display_avatar.url,
    )
    return embed

def QueueEmbed(queue: wavelink.Queue) -> discord.Embed:
    embed = discord.Embed(title="Queue")
    for i in range(min(25, queue.count)):
        title = str(i+1) + ". " + queue.peek(i).title
        artist = queue.peek(i).author
        embed.add_field(name=title, value=artist, inline=False)
    return embed
