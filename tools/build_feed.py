#!/usr/bin/env python3
"""Build a podcast RSS feed from the episode MP3s in a site folder.

Usage: build_feed.py SITE_DIR BASE_URL
SITE_DIR has episodes/YYYY-MM-DD.mp3 and optional episodes/YYYY-MM-DD.title (one line).
Writes SITE_DIR/feed.xml. Keeps the newest 60 episodes in the feed.
"""
import datetime, email.utils, os, subprocess, sys


def mp3_duration_estimate(path):
    """Duration from the first MPEG frame's bitrate; fine for constant-bitrate TTS audio."""
    data = open(path, "rb").read()
    i = 0
    if data[:3] == b"ID3":
        i = 10 + ((data[6] & 0x7f) << 21 | (data[7] & 0x7f) << 14 | (data[8] & 0x7f) << 7 | (data[9] & 0x7f))
    while i < len(data) - 4:
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            ver = (data[i + 1] >> 3) & 3
            idx = data[i + 2] >> 4
            v1 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
            v2 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
            kbps = (v1 if ver == 3 else v2)[idx]
            if kbps:
                return str((len(data) - i) * 8 / (kbps * 1000))
        i += 1
    return "0"


def probe_duration(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.strip()
        if out:
            return out
    except FileNotFoundError:
        pass
    return mp3_duration_estimate(path)

from xml.sax.saxutils import escape

site, base = sys.argv[1], sys.argv[2].rstrip("/")
eps = sorted((f[:-4] for f in os.listdir(os.path.join(site, "episodes")) if f.endswith(".mp3")), reverse=True)[:60]
items = []
for d in eps:
    mp3 = os.path.join(site, "episodes", d + ".mp3")
    tf = os.path.join(site, "episodes", d + ".title")
    title = open(tf).read().strip() if os.path.exists(tf) else "Modern Battlefield brief"
    dt = datetime.datetime.strptime(d, "%Y-%m-%d").replace(hour=9, tzinfo=datetime.timezone.utc)
    dur = probe_duration(mp3)
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
