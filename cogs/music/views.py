from typing import Union
import disnake, wavelink


def NowPlayingEmbed(
    track: wavelink.YouTubeTrack, author: Union[disnake.User, disnake.Member]
) -> disnake.Embed:
    description = f"```[{track.title}]({track.uri})```"
    requested = f"Requested by {author.display_name}"
    embed = disnake.Embed(title="Now Playing", description=description)
    embed.set_thumbnail(track.thumbnail)
    embed.set_image(
        url="https://cutewallpaper.org/21/music-equalizer-gif/Tag-For-Music-Equalizer-Gif-45x11cm-Music-Rhythm-Led-Car-.gif"
    )
    embed.set_footer(text=requested, icon_url=author.display_avatar.url)
    return embed
