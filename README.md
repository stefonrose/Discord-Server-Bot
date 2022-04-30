### Discord Server Bot (a.k.a. Sinful Server Bot)

This is a bot I created for a discord server that my friends and I share. The initial goal of the bot is to play music when given a song title or link. Additional features will be added as needed and documented in this readme.

#### Roadmap

- [ ] API Connections
  - [ ] Connect with YouTube API
  - [ ] Connect with Spotify API
  - [ ] Connect with Soundcloud API
- [ ] Implement slash commands
  - [ ] **Play** or queue a song based on the text entered
    - [ ] Use regex to determine if the text is a link
      - [ ] If it is a link, then check if it is a YouTube, Spotify or Soundcloud link. If it is not one of those then return confusion. If the link is a song, play or queue it. If it is a playlist, then queue all the songs in the playlist.
      - [ ] If the text is not a link then perform a search on youtube and return the top result. (Possibly have this default to the lyric version so that music videos are skipped. But also have a separate Playtop command that plays the top result)
  - [ ] **Pause** the current song
  - [ ] **Skip** to the next song in the queue
  - [ ] **Display** songs in queue
  - [ ] Play the server **mix**
