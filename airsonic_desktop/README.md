

Faq:

Why isn't gapless playback working for me?

One thing to try is to configure your airsonic server to transcode to opus. Opus uses Ogg, which is a much better specified music container format than MP3. This means that mpv has to spend much less time reading the stream to determine what kind of audio it is.