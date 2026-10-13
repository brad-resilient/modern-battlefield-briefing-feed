#!/usr/bin/env python3
"""Build a podcast RSS feed from the episode MP3s in a site folder.

Usage: build_feed.py SITE_DIR BASE_URL
SITE_DIR has episodes/YYYY-MM-DD.mp3 and optional episodes/YYYY-MM-DD.title (one line).
Writes SITE_DIR/feed.xml. Keeps the newest 60 episodes in the feed.
"""
import datetime, email.utils, os, subprocess, sys
from xml.sax.saxutils import escape

site, base = sys.argv[1], sys.argv[2].rstrip("/")
eps = sorted((f[:-4] for f in os.listdir(os.path.join(site, "episodes")) if f.endswith(".mp3")), reverse=True)[:60]
items = []
for d in eps:
    mp3 = os.path.join(site, "episodes", d + ".mp3")
    tf = os.path.join(site, "episodes", d + ".title")
    title = open(tf).read().strip() if os.path.exists(tf) else "Modern Battlefield brief"
    dt = datetime.datetime.strptime(d, "%Y-%m-%d").replace(hour=9, tzinfo=datetime.timezone.utc)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                         capture_output=True, text=True).stdout.strip() or "0"
    nice = dt.strftime("%A, %B ") + str(dt.day)
    items.append(f"""<item><title>{escape(nice + ': ' + title)}</title><guid isPermaLink="false">modern-battlefield-{d}</guid>
<pubDate>{email.utils.format_datetime(dt)}</pubDate><enclosure url="{base}/episodes/{d}.mp3" length="{os.path.getsize(mp3)}" type="audio/mpeg"/>
<itunes:duration>{int(float(dur))}</itunes:duration><description>{escape(title)}</description></item>""")
feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel><title>Modern Battlefield Brief</title><link>{base}/</link><language>en-us</language>
<description>Daily briefing on drone warfare, combat casualty care, warfighter wearables, counter-drone, and the defense tech market.</description>
<itunes:author>Modern Battlefield Brief</itunes:author><itunes:block>Yes</itunes:block><itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
</channel></rss>
"""
open(os.path.join(site, "feed.xml"), "w").write(feed)
print(f"feed.xml with {len(items)} episodes")
