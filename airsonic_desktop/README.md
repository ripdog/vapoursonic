

Faq:

Why isn't gapless playback working for me?

One thing to try is to configure your airsonic server to transcode to opus. Opus uses Ogg, which is a much better specified music container format than MP3. This means that mpv has to spend much less time reading the stream to determine what kind of audio it is.

Known Issues:

HTTP requests do not attempt IPv6 and v4 simultaneously (happy eyeballs). 
This means that if you have a working v6 connection and your server has a broken v6 address advertised in DNS, all requests to your server will be extremely slow. 
Fix or remove the v6 record in your server DNS to fix.