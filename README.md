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

MIA only cares about three categories of request codes:

1. Redirects, because these are displayed specially in the UI
2. Various OKs, basically the entire 100- and 200-series
3. Errors, which are either ignored or result in archival errors

If you need precision archival, there's other tools more suited for that, and I do not understand enough to even begin to approximate an implementation.

### Why roll your own?

Two main reason, the first being that I can. I need this kind of software, and with ArchiveBox no longer being an option, this was the only way.

The second, and the arguably better and more broadly applicable reason, is that archival appears to have been somewhat underprioritised in open-source.

Archive.org, archive.is, and many of the other major archives currently in used are closed-source. Archive.org is the more legal one of these[^2], and in spite of this, several industries have gone after archive.org with lawsuits. Lawsuits are expensive, especially when the two parties are a donation-driven non-profit, and for-profit organisations with seemingly bottomless lawyer funds and an almost certainly unhealthy love for litigation.

The combination of a few huge, closed-source archives and lawsuits means archival is constantly being threatened. If these actors disappear (read: get sued into oblivion), publicly available archival software also risks disappearing.

Though MIA will never be able to operate at that scale, it is at least designed to work well for private archival use. You won't find an (officially endorsed) public MIA instance anywhere. It is also one of only two archival tools I'm aware of meeting this particular niche, with the other being ArchiveBox. [ArchiveBox has a list of competitors](https://github.com/ArchiveBox/ArchiveBox/wiki/Web-Archiving-Community#other-archivebox-alternatives), and of these, precisely 0 are the same kind of software as ArchiveBox and MIA. There's WARC, there's bookmark managers (quite a few actually, and they're only archiving in the sense that they try to create a local copy), notetaking tools, and other archival utilities, but no full, proper archives. Precisely 0 of these archives then go on to work around aggressive Cloudflare configurations that block private archives, but not private access.

But there should be more full archives on the list. MIA is my contribution - and I do hope much better alternatives appear eventually.

## Implementation technicalities

### Cloudflare and `robots.txt`

When Stack Exchange drastically increased how aggressive they configured Cloudflare, it resulted in people being locked out, or forced to go through very regular Cloudflare checks due to browser configuration details. Legitimate users were inconvenienced or blocked by systems meant to block AI scrapers - they were collateral damage. Same with many scripts by powerusers that make the site possible to moderate or use efficiently.

This has happened in quite a few places around the web, and unfortunately, it means that private archives are heavily affected. Archive.org often gets a pass because it's a big, centralised instance on several whitelists. Cloudflare maintains a list of "verified bots"[^3], which the Internet Archive is on, but getting on that list is a Whole Thing:tm:. There's a minimum requirement of 1000 requests per day, and that the IP(s) provided for the service are exclusively used for that service[^4]. If all you're doing is running a self-hosted archive so you don't lose access to the sites you care about, you're probably going to fail both these criteria. I self-host my instance, and my IP is used for all kinds of things, so I would be breaching that policy even if I did somehow manage 1000 requests/day.

In lieu of being able to say "I'm a bot operating on the explicit instructions of a human", the decision was made to apply various techniques for avoiding Cloudflare. `undetected-geckodriver-lw` is used to force the browser not to identify itself as automated, and certain very basic stepes are taken to automatically resolve Cloudflare checks if they're encountered. `robots.txt` is not respected either, since the services with very aggressive CF configurations don't respect me as a user in a non-automated context anyway.

As for robots.txt in particular, [archive.is has a similar rationale](https://archive.is/faq). The crawls are primarily intended to be either triggered by a human, or triggered by a human by proxy, so robots.txt doesn't need to be respected. This behaviour is consistent with many other archival and non-archival applications.

I apply a similar rationale to Cloudflare. The requests are manually made for someone who self-hosts MIA, so within reason trying to work around Cloudflare is not something I see as a problem. The attempted workaround is simply clicking the checkbox and seeing if that's good enough for the captcha, which is what a human would've done if they sat interacting with the archival process anyway. Since the goal is to implement an extended version of `<Ctrl-S>` in browsers, and that stores it in a sane format automatically, it's not far-fetched that this is something someone could do manually anyway.

## Requirements and setup

To set up MIArchive, you need:

* A Linux-based server
* Python 3.10+
* Postgresql, not necessarily installed on the same machine

For development setup, see [CONTRIBUTING.md](CONTRIBUTING.md). The README only details how to install MIArchive for production use.

### Automated setup



[^1]: Yes, this is a pun on Missing In Action and Archival/Archive (Missing In Archive is functionally the canonical full name). Yes, I thought I was funny. Yes, I'm already regretting my decision (mostly, it does at least give nice, shortly typed `mia` commands). Yes, I still think I'm funny several days later, even after needing to fork `selenium-wire-2`.
[^2]: I'm not saying the others are illegal, but as far as I know, archive.org goes a lot further than many other archives in making sure the content hosted is legal. This unfortunately means archive.org is fairly quick to take down content, which makes it hard to actually preserve the historical record.
[^3]: [This list](https://radar.cloudflare.com/bots#verified-bots) is absolute bullshit. It includes OpenAI, Google's slop bot, anthropic, and Meta (Facebook), all of whom have questionable relations to respecting requests not steal data, and questionable relations [to basic copyright law](https://arstechnica.com/tech-policy/2025/02/meta-torrented-over-81-7tb-of-pirated-books-to-train-ai-authors-say/)
[^4]: https://developers.cloudflare.com/bots/concepts/bot/verified-bots/policy/
