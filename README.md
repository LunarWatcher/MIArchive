# MIArchive[^1]

A quick and dirty archival system meant as a replacement for my use of [ArchiveBox](https://github.com/ArchiveBox/ArchiveBox), featuring:

* undetected-geckodriver with ublock by default. Self-hosted archives have been especially vulnerable to aggressive Cloudflare configurations that block anything that maybe perhaps vaguely looks like it could be an AI slop scraper.
* More of archive.org-like interface, where recapturing sites isn't a second-class activity shoehorned in after the fact.

Unlike ArchiveBox, MIArchive is intentionally designed to not store as many formats. Though certain additional downloaders exist, for websites, the goal is to store websites. If you want to download YouTube videos, [there's a perfectly good program for that](https://github.com/yt-dlp/yt-dlp).

Also unlike ArchiveBox, MIA is Linux-only, largely to take advantage of some Linux-only features.

## Untitled tangent section

The main target pages for the archiver is relatively simple pages, meaning pages where things load fairly easily. Archiving a full SPA, for example, is never going to be as good as archiving a more conventional website. Large amounts of dynamic content heavily dependent on API requests that aren't called during the page load never works well, at least not with any archives I'm aware of.

Trying to support these to archive every single website in the greatest detail possible simply isn't a goal of this archiver. That's part of why I have no plans to support  WARC. That and WARC doesn't seem to trivially integrate with selenium, from a few very quick searches. I care more about preserving information than preserving every cursed website setup there is. Instead, MIA focuses more on actually getting to the content. Ads can fuck right off, and Cloudflare can too. This may be an unacceptable tradeoff for a good few kinds of archivists out there, but it's perfectly acceptable for my use.

ArchiveBox, as far as I can tell, has plans to handle stuff like this better, but its goals are also very different from MIA's goals. Unforunately, development has halted for the foreseeable future, as its main developer had to earn money. That is what caused this project to start existing; the internet is growing increasingly locked-down, which makes third-party archival increasingly more difficult. At the same time, centralised archives (notably archive.org) is under immense pressure from anti-archival capitalists with sizeable lawyer funds. I don't have months to wait for ArchiveBox to maybe become usable again. 

### Why not support WARC?

WARC is designed to reproduce websites down to the request level, while MIA is designed to store websites in a usable format. 

This means, among other things, taking steps that appear to be incompatible with a WARC, or require nasty hacks that could've just been a monolithic-ish page. Again, this is a sacrifice in the accuracy of the reproduction of the page designed to preserve the usability of the page. 

WARC support may be added in the future if there's suddenly interest in adding it, but I won't be adding it speculatively in case someone really wants WARCs.



## Requirements and setup

[^1]: Yes, this is a pun on Missing In Action and Archival. Yes, I thought I was funny. Yes, I'm already regretting my decision (mostly, it does at least give nice, shortly typed `mia` commands)
