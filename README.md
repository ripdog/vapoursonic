vapoursonic
=

vapoursonic is a simple PyQt5+mpv based player for [Airsonic](https://github.com/airsonic/airsonic) servers. It is licensed under the GPLv3.

It is designed to run in the background while you work, using little CPU or RAM resources. On Windows and Linux, it integrates nicely into your OS, with taskbar progress/buttons and media keys on Windows, and MPRIS on Linux.

The app is still rather incomplete. The code is a bit of a mess, and error handling is limited. Keep that in mind if you try it out.

_*Non HTTPS server?*_

I have tried to add support for non-https airsonic servers, but my airsonic server is https-only (as yours should be) so I couldn't test this. Do file an issue if it doesn't work.

Help wanted!
--

As you can see, the app and logo are both kinda ugly. I'm not a designer and I don't have a creative bone in my body. If you have any talent in these areas, I would be incredibly grateful if you could assist with improvements! Thank you! 

FAQ:
--
_What platforms does it run on?_

All the technologies I've built on are cross-platform, across at least Windows, Linux, and MacOS. There is solid support for OS integration with Windows and Linux.

MacOS? Should work. I don't have a mac though, so no integration nor builds will be happening.

_Why isn't gapless playback working for me?_

vapoursonic uses mpv to play your music. mpv uses ffmpeg in turn, which errs on the side of 'working right' rather than 'working fast'.

One way this manifests is that mpv will always detect the file format of music passed to it. It will keep reading and scanning more and more of the file until it is sufficiently sure that it knows the file format of the music before it attempts to play it.

This causes problems when your music is being transcoded to (or is delivered natively as) MP3, as MP3 is a very difficult format to detect. In my testing, mpv often had to take 3-4 reads of MP3 files to get sufficient confidence that it had detected it correctly, leading to an audible delay between songs.

One thing to try is to configure your airsonic server to transcode to opus. Opus uses Ogg, which is a much better specified music container format than MP3. I found that ogg can be reliably detected in the first read, leading to excellent gapless playback. Also, opus is the best audio codec around right now, and patent unencumbered to boot. If you're transcoding, opus is an excellent choice for many reasons.

Obviously transcoding isn't great for audio quality, especially if your files are lossy to begin with. Still, with an opus transcode at 192kbps, you will not notice the difference.
***
Known Issues:

HTTP requests do not attempt IPv6 and v4 simultaneously (happy eyeballs). 
This means that if you have a working v6 connection and your server has a broken v6 address advertised in DNS, all requests to your server will be extremely slow. 
Fix or remove the v6 record in your server DNS to fix.

Development environment
---

vapoursonic uses [Poetry](https://python-poetry.org) to manage dependencies and [fman build system](https://build-system.fman.io/).

You must use Python 3.6.8.

To set up a dev environment, install poetry, clone this repo, use `poetry env use python3.6` to inform poetry about your python version, and run `poetry install` in the repo. Then you should be able to run `poetry shell` and then `fbs run` to run it. 

To build, run `fbs freeze` then `fbs installer`. On windows you need [nsis](https://nsis.sourceforge.io/Download) installed to make an installer. 
