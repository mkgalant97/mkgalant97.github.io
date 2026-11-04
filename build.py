#!/usr/bin/env python3
"""Static site generator for Misha Galant's website.

Edit the files in data/, then run:  python3 build.py          (writes docs/)
                                    python3 build.py --serve  (build + local preview)
"""
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
DATA = ROOT / "data"

# "" when the site lives at the root of its domain (mkgalant97.github.io or a custom domain).
BASE_PATH = ""
CUSTOM_DOMAIN = ""  # e.g. "www.mishagalant.com" once a domain is pointed at GitHub Pages
SITE_URL = "https://mkgalant97.github.io"
CSS_VERSION = hashlib.md5((ROOT / "assets" / "style.css").read_bytes()).hexdigest()[:8]
YEAR = dt.date.today().year

content = json.loads((DATA / "content.json").read_text("utf-8"))
events = json.loads((DATA / "events.json").read_text("utf-8"))
videos = json.loads((DATA / "videos.json").read_text("utf-8"))
trips = json.loads((DATA / "trips.json").read_text("utf-8"))

NAV = [
    ("home", "Home", "/"),
    ("bio", "Biography", "/biography/"),
    ("schedule", "Schedule", "/schedule/"),
    ("videos", "Videos", "/videos/"),
    ("mountains", "Mountains", "/mountains/"),
    ("lessons", "Lessons", "/lessons/"),
    ("contact", "Contact", "/contact/"),
]

e = html.escape

# ---------------------------------------------------------------- icons
ICONS = {
    "facebook": '<path d="M14 8.5V6.8c0-.8.2-1.3 1.4-1.3H17V2.2C16.7 2.1 15.6 2 14.4 2 11.8 2 10.5 3.6 10.5 6.3v2.2H8V12h2.5v10H14V12h2.6l.4-3.5z"/>',
    "youtube": '<path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8zM10 15V9l5.2 3L10 15z"/>',
    "linkedin": '<path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.5h4V21H3V9.5zm6.5 0h3.8v1.6h.1c.5-1 1.8-2 3.8-2 4 0 4.8 2.6 4.8 6V21h-4v-5.2c0-1.2 0-2.8-1.7-2.8s-2 1.3-2 2.7V21h-4V9.5z"/>',
    "strava": '<path d="M15.4 17.3l-2.1-4.1h-3l5.1 10 5-10h-3l-2 4.1zM10.2 2 3.4 15.3h4.1l2.7-5.3 2.7 5.3H17L10.2 2z"/>',
    "mail": '<path d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm9 7.2L4.5 7H4v.6l8 5.6 8-5.6V7h-.5L12 12.2z"/>',
}
SOCIAL_LABELS = {"facebook": "Facebook", "youtube": "YouTube", "linkedin": "LinkedIn", "strava": "Strava"}


def icon(name, size=20):
    return f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" aria-hidden="true" fill="currentColor">{ICONS[name]}</svg>'


def social_links(cls="social"):
    items = "".join(
        f'<a href="{e(url)}" target="_blank" rel="noopener" aria-label="{SOCIAL_LABELS[k]}">{icon(k)}</a>'
        for k, url in content["social"].items()
    )
    return f'<div class="{cls}">{items}</div>'


# Five lines that ripple like contour lines: a musical staff drawn as a mountain ridge.
STAFF_SVG = (
    '<svg class="staff" viewBox="0 0 1200 60" preserveAspectRatio="none" aria-hidden="true">'
    + "".join(
        f'<path d="M0 {12 + i*9} C 200 {2 + i*9}, 340 {26 + i*9}, 520 {14 + i*9} S 860 {0 + i*9}, 1000 {16 + i*9} S 1140 {22 + i*9}, 1200 {12 + i*9}"/>'
        for i in range(5)
    )
    + "</svg>"
)

# ---------------------------------------------------------------- page shell


def with_base(doc):
    if not BASE_PATH:
        return doc
    return re.sub(r'(href|src|action)="/(?!/)', rf'\1="{BASE_PATH}/', doc).replace("url(/", f"url({BASE_PATH}/")


def page(path, title, body, active=None, description="", body_class="", scripts=""):
    nav = "".join(
        f'<a href="{href}"{" class=\"active\" aria-current=\"page\"" if key == active else ""}>{label}</a>'
        for key, label, href in NAV
    )
    full_title = "Misha Galant | Pianist" if active == "home" else f"{title} | Misha Galant"
    desc = description or "Misha Galant, pianist: biography, concert schedule, performance videos, lessons and mountain adventures."
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE_URL}{BASE_PATH}/assets/img/hero-lake-blanche.jpg">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={CSS_VERSION}">
</head>
<body class="{body_class}">
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/"><span class="brand-name">Misha Galant</span><span class="brand-role">Pianist</span></a>
    <button class="menu-toggle" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="site-nav">{nav}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  {STAFF_SVG}
  <div class="wrap footer-inner">
    <div>
      <p class="footer-name">Misha Galant</p>
      <p class="footer-sub">Pianist · Salt Lake City</p>
    </div>
    <nav class="footer-nav">{"".join(f'<a href="{h}">{l}</a>' for _, l, h in NAV)}</nav>
    {social_links("social footer-social")}
  </div>
  <p class="copyright">© {YEAR} Misha Galant. All rights reserved.</p>
</footer>
<script>
document.querySelector('.menu-toggle').addEventListener('click', function () {{
  var open = document.body.classList.toggle('nav-open');
  this.setAttribute('aria-expanded', open);
}});
</script>
{scripts}
</body>
</html>
"""
    target = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(with_base(doc), "utf-8")


def page_head(title, kicker="", lead="", image=None):
    style = f' style="background-image:linear-gradient(180deg,rgba(18,32,25,.35),rgba(18,32,25,.75)),url({image})"' if image else ""
    cls = "page-head has-image" if image else "page-head"
    return f"""<section class="{cls}"{style}>
  <div class="wrap">
    {f'<p class="kicker">{kicker}</p>' if kicker else ''}
    <h1>{title}</h1>
    {f'<p class="lead">{lead}</p>' if lead else ''}
  </div>
  {STAFF_SVG}
</section>"""


# ---------------------------------------------------------------- helpers


def first_text(fragment, limit=150):
    for p in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", fragment, flags=re.S):
        if "trip-link" in p:
            continue
        t = re.sub(r"<figure.*?</figure>", "", p, flags=re.S)
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()
        if len(t) > 40:
            if len(t) > limit:
                t = t[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
            return t
    return ""


def trip_card(t):
    frag = (DATA / "trips" / f"{t['slug']}.html").read_text("utf-8")
    return f"""<a class="trip-card" href="/mountains/{t['slug']}/">
  <div class="trip-img"><img src="/assets/img/trips/{t['cover']}" alt="{e(t['title'])}" loading="lazy"></div>
  <div class="trip-body">
    <p class="trip-date">{e(t['date'])}</p>
    <h3>{e(t['title'])}</h3>
    <p>{e(first_text(frag))}</p>
  </div>
</a>"""


def video_card(v):
    return f"""<figure class="video">
  <button class="yt" data-id="{v['id']}" aria-label="Play {e(v['composer'])}: {e(v['work'])}" style="background-image:url(https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg)">
    <span class="play"><svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.3.3 34 .3 34 .3s-21.3 0-26.5 1.4a8.5 8.5 0 0 0-6 6A88 88 0 0 0 .1 24a88 88 0 0 0 1.4 16.3 8.5 8.5 0 0 0 6 6C12.7 47.7 34 47.7 34 47.7s21.3 0 26.5-1.4a8.5 8.5 0 0 0 6-6A88 88 0 0 0 67.9 24a88 88 0 0 0-1.4-16.3z" fill="#c4302b"/><path d="M45 24 27 14v20z" fill="#fff"/></svg></span>
  </button>
  <figcaption><span class="composer">{e(v['composer'])}</span>{e(v['work'])}</figcaption>
</figure>"""


VIDEO_SCRIPT = """<script>
document.querySelectorAll('.yt').forEach(function (b) {
  b.addEventListener('click', function () {
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + b.dataset.id + '?autoplay=1&rel=0';
    f.title = b.getAttribute('aria-label');
    f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
    f.allowFullscreen = true;
    b.replaceWith(f);
  });
});
</script>"""


# ---------------------------------------------------------------- pages


def build_home():
    news = "".join(
        f'<li><a href="{e(n["url"])}" target="_blank" rel="noopener"><span class="news-title">{e(n["title"])}</span><span class="news-source">{e(n["source"])} ↗</span></a></li>'
        for n in content["news"]
    )
    body = f"""
<section class="hero">
  <div class="hero-img" style="background-image:url(/assets/img/hero-lake-blanche.jpg)"></div>
  <div class="wrap hero-inner">
    <p class="kicker">Salt Lake City</p>
    <h1>Misha Galant</h1>
    <p class="hero-role">Pianist</p>
    <div class="hero-actions">
      <a class="btn btn-light" href="/videos/">Watch performances</a>
      <a class="btn btn-ghost" href="/biography/">Biography</a>
    </div>
  </div>
  {STAFF_SVG}
</section>

<section class="section intro">
  <div class="wrap intro-grid">
    <div class="intro-photo"><img src="/assets/img/portrait.jpg" alt="Misha Galant"></div>
    <div class="intro-text">
      <p class="kicker">Welcome</p>
      <h2>Music, mountains, and everything in between</h2>
      <p>{e(content["home_intro"])}</p>
      <a class="text-link" href="/biography/">Read the full biography →</a>
    </div>
  </div>
</section>

<section class="section listen">
  <div class="wrap listen-grid">
    <figure class="listen-photo">
      <img src="/assets/img/fort-worth-symphony.jpg" alt="Misha Galant performing with the Fort Worth Symphony Orchestra" loading="lazy">
      <figcaption>With the Fort Worth Symphony Orchestra. Photo courtesy of PianoTexas, 2018.</figcaption>
    </figure>
    <div class="listen-text">
      <p class="kicker">Listen</p>
      <h2>Rachmaninoff, Piano Concerto no. 3</h2>
      <p>The closing pages of the third concerto, live with the Fort Worth Symphony Orchestra.</p>
      <audio controls preload="none" src="/assets/audio/rach3-ending.mp3"></audio>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div><p class="kicker">Watch</p><h2>Recent performances</h2></div>
      <a class="text-link" href="/videos/">All videos →</a>
    </div>
    <div class="video-grid three">{"".join(video_card(v) for v in videos[:3])}</div>
  </div>
</section>

<section class="section tinted">
  <div class="wrap two-col">
    <div>
      <p class="kicker">In the news</p>
      <h2>Press</h2>
      <ul class="news">{news}</ul>
    </div>
    <div class="support-card">
      <p class="kicker">Support</p>
      <h2>Support my music</h2>
      <p>If you'd like to support my musical endeavors, you can make a contribution through PayPal. Thank you!</p>
      <form action="https://www.paypal.com/donate" method="post" target="_blank">
        <input type="hidden" name="business" value="{e(content['paypal_business_id'])}">
        <input type="hidden" name="currency_code" value="USD">
        <button class="btn" type="submit">Donate with PayPal</button>
      </form>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div><p class="kicker">Beyond the keyboard</p><h2>From the mountains</h2></div>
      <a class="text-link" href="/mountains/">All adventures →</a>
    </div>
    <div class="trip-grid">{"".join(trip_card(t) for t in trips if t['slug'] in ('devils-castle', 'state-high-points', 'half-dome'))}</div>
  </div>
</section>
"""
    page("/", "Home", body, "home", body_class="home", scripts=VIDEO_SCRIPT)


def build_bio():
    paras = content["biography"]
    text = "".join(f"<p>{e(p)}</p>" for p in paras)
    body = f"""{page_head("Biography", "About")}
<section class="section">
  <div class="wrap bio-grid">
    <div class="bio-photo"><img src="/assets/img/portrait.jpg" alt="Misha Galant"></div>
    <div class="bio-text prose">{text}</div>
  </div>
</section>"""
    page("/biography/", "Biography", body, "bio", description=paras[0][:155])


def event_item(ev):
    d = dt.date.fromisoformat(ev["date"])
    program = "".join(f'<li><strong>{e(p["composer"])}</strong> {e(p["work"])}</li>' for p in ev["program"])
    with_ = "".join(f"<li>{e(w)}</li>" for w in ev.get("with", []))
    link = f'<a class="text-link" href="{e(ev["link"]["url"])}" target="_blank" rel="noopener">{e(ev["link"]["label"])} ↗</a>' if ev.get("link") else ""
    return f"""<li class="event" data-date="{ev['date']}">
  <div class="event-date"><span class="day">{d.day}</span><span class="month">{d.strftime('%b %Y')}</span></div>
  <div class="event-main">
    <p class="event-when">{e(ev['display_date'])}{' · ' + e(ev['time']) if ev.get('time') else ''}</p>
    <h3>{e(ev['title'])}</h3>
    <ul class="program">{program}</ul>
    {link}
  </div>
  <div class="event-side">
    <p class="event-venue">{e(ev['venue'])}</p>
    <p class="event-city">{e(ev['city'])}</p>
    {f'<ul class="with">{with_}</ul>' if with_ else ''}
  </div>
</li>"""


def build_schedule():
    today = dt.date.today().isoformat()
    upcoming = sorted([ev for ev in events if ev.get("end", ev["date"]) >= today], key=lambda x: x["date"])
    past = sorted([ev for ev in events if ev.get("end", ev["date"]) < today], key=lambda x: x["date"], reverse=True)
    empty = '<p class="empty">New dates will be announced soon. For booking inquiries, please <a href="/contact/">get in touch</a>.</p>'
    body = f"""{page_head("Schedule", "Concerts")}
<section class="section">
  <div class="wrap narrow-wrap">
    <h2 class="list-title">Upcoming</h2>
    {f'<ul class="events">{"".join(event_item(x) for x in upcoming)}</ul>' if upcoming else empty}
    <h2 class="list-title">Past performances</h2>
    <ul class="events past">{"".join(event_item(x) for x in past)}</ul>
  </div>
</section>"""
    page("/schedule/", "Schedule", body, "schedule")


def build_videos():
    body = f"""{page_head("Videos", "Watch", "A selection of performance videos. The full collection is on my YouTube channel.")}
<section class="section">
  <div class="wrap">
    <div class="video-grid">{"".join(video_card(v) for v in videos)}</div>
    <p class="center"><a class="btn" href="{e(content['social']['youtube'])}" target="_blank" rel="noopener">{icon('youtube')} Visit my YouTube channel</a></p>
  </div>
</section>"""
    page("/videos/", "Videos", body, "videos", scripts=VIDEO_SCRIPT)


def build_mountains():
    body = f"""{page_head("Mountains", "Beyond the keyboard", e(content["mountains_intro"]), "/assets/img/fall-utah.jpg")}
<section class="section">
  <div class="wrap">
    <div class="trip-grid">{"".join(trip_card(t) for t in trips)}</div>
  </div>
</section>"""
    page("/mountains/", "Mountains", body, "mountains")

    for i, t in enumerate(trips):
        frag = (DATA / "trips" / f"{t['slug']}.html").read_text("utf-8")
        prev_t, next_t = trips[i - 1], trips[(i + 1) % len(trips)]
        body = f"""{page_head(e(t['title']), e(t['date']) or "Trip report", image=f"/assets/img/trips/{t.get('banner', t['cover'])}")}
<article class="section">
  <div class="wrap trip-article prose">
    <p class="crumbs"><a href="/mountains/">← All adventures</a></p>
    {frag}
  </div>
  <nav class="wrap trip-pager">
    <a href="/mountains/{prev_t['slug']}/"><span>Previous</span>{e(prev_t['title'])}</a>
    <a href="/mountains/{next_t['slug']}/"><span>Next</span>{e(next_t['title'])}</a>
  </nav>
</article>"""
        page(f"/mountains/{t['slug']}/", t["title"], body, "mountains", description=first_text(frag, 155),
             body_class="trip")


def form_embed(form_id, height):
    url = f"https://docs.google.com/forms/d/e/{form_id}/viewform?embedded=true"
    return f"""<div class="form-card">
  <iframe src="{url}" height="{height}" title="Form" loading="lazy">Loading…</iframe>
  <p class="form-fallback">Form not loading? <a href="{url.replace('?embedded=true', '')}" target="_blank" rel="noopener">Open it in a new tab ↗</a></p>
</div>"""


def build_lessons():
    body = f"""{page_head("Lessons", "Teaching", "I teach piano to students of all ages and levels. To apply for lessons, fill out the form below and I'll be in touch.")}
<section class="section">
  <div class="wrap narrow-wrap">{form_embed(content['lessons_form'], 1600)}</div>
</section>"""
    page("/lessons/", "Lessons", body, "lessons")


def build_contact():
    body = f"""{page_head("Contact", "Get in touch")}
<section class="section">
  <div class="wrap contact-grid">
    <div class="contact-info">
      <h2>Say hello</h2>
      <p>For performance inquiries, collaborations, or anything else, send a message using the form or email me directly.</p>
      <p><a class="contact-email" href="mailto:{e(content['email'])}">{icon('mail')} {e(content['email'])}</a></p>
      {social_links("social social-dark")}
    </div>
    <div>{form_embed(content['contact_form'], 1100)}</div>
  </div>
</section>"""
    page("/contact/", "Contact", body, "contact")


def build_404():
    body = f"""{page_head("Page not found", "404", "The trail ends here. Try the <a href='/'>home page</a> instead.")}"""
    page("/404/", "Page not found", body)
    (OUT / "404.html").write_text((OUT / "404" / "index.html").read_text("utf-8"), "utf-8")
    shutil.rmtree(OUT / "404")


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    css = OUT / "assets" / "style.css"
    css.write_text(with_base(css.read_text("utf-8")), "utf-8")
    (OUT / ".nojekyll").write_text("")
    if CUSTOM_DOMAIN:
        (OUT / "CNAME").write_text(CUSTOM_DOMAIN + "\n")
    build_home()
    build_bio()
    build_schedule()
    build_videos()
    build_mountains()
    build_lessons()
    build_contact()
    build_404()
    # Old Columbia URLs (about.html, schedule.html, ...) keep working.
    redirects = {"index.html": None, "about.html": "/biography/", "schedule.html": "/schedule/",
                 "videos.html": "/videos/", "mountains.html": "/mountains/", "lessons.html": "/lessons/",
                 "contact.html": "/contact/"}
    redirects.update({t["old_page"]: f"/mountains/{t['slug']}/" for t in trips})
    for old, new in redirects.items():
        if new:
            (OUT / old).write_text(with_base(
                f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={new}">'
                f'<link rel="canonical" href="{new}"><a href="{new}">Moved here</a>'), "utf-8")
    print(f"Built {sum(1 for _ in OUT.rglob('*.html'))} pages into {OUT}")


def serve():
    import functools, http.server, socketserver, tempfile
    tmp = Path(tempfile.mkdtemp())
    root = tmp / BASE_PATH.strip("/") if BASE_PATH else tmp
    root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(OUT, root, dirs_exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp))
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print(f"Preview: http://localhost:8000{BASE_PATH}/   (Ctrl+C to stop)")
        httpd.serve_forever()


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        serve()
