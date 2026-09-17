### Discord Server Bot
This is a bot I created for a discord server that my friends and I share. The initial goal of the bot is to play music when given a song title or link. Additional features will be added as needed and documented in this readme.

#### Roadmap

- [ ] Music Service Connections
  - [x] Connect with YouTube
  - [x] Connect with Spotify
  - [ ] Connect with Apple Music
  - [ ] Connect with Soundcloud
- [ ] Implement slash commands
  - [x] **Play** or queue a song based on the text entered
    - [x] Use regex to determine if the text is a link
      - [x] If it is a link, then check if it is a YouTube, Spotify or Soundcloud link. If it is not one of those then return confusion. If the link is a song, play or queue it. If it is a playlist, then queue all the songs in the playlist.
      - [x] If the text is not a link then perform a search on youtube and return the top result.
  - [x] **Pause** the current song
  - [x] **Skip** to the next song in the queue
  - [x] **Display** songs in queue
  - [ ] Play the server **mix**
