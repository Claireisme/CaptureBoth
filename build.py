#!/usr/bin/env python3
"""Build the multilingual, dependency-free Cloudflare Pages site."""
import hashlib
import html
import json
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = HERE / "dist"
CONFIG = json.loads((HERE / "site.config.json").read_text())
APP_POLICY = ROOT / "CaptureBoth/Resources/PrivacyPolicy.json"
POLICY_PATH = APP_POLICY if APP_POLICY.is_file() else HERE / "data/privacy-policy.json"
PROJECT_ROOT = ROOT if APP_POLICY.is_file() else HERE
ARCHIVE_PATH = PROJECT_ROOT / "release/CaptureBoth-Cloudflare-Pages.zip"
POLICY = json.loads(POLICY_PATH.read_text())

LANGUAGES = {
    "en": {"name": "English", "path": "", "screenshots": "en"},
    "fr": {"name": "Français", "path": "fr", "screenshots": "en"},
    "it": {"name": "Italiano", "path": "it", "screenshots": "en"},
    "de": {"name": "Deutsch", "path": "de", "screenshots": "en"},
    "es": {"name": "Español", "path": "es", "screenshots": "en"},
    "ja": {"name": "日本語", "path": "ja", "screenshots": "en"},
    "ko": {"name": "한국어", "path": "ko", "screenshots": "en"},
    "pt": {"name": "Português", "path": "pt", "screenshots": "en"},
    "zh-Hant": {"name": "繁體中文", "path": "zh-hant", "screenshots": "en"},
}
COPY = {}
PRIVACY = {}
POLICY_SOURCE_HASH = hashlib.sha256(json.dumps(POLICY["localizations"]["en"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
for language in LANGUAGES:
    file = HERE / "locales" / (language + ".json")
    data = json.loads(file.read_text())
    if language in POLICY["localizations"]:
        PRIVACY[language] = POLICY["localizations"][language]
    else:
        if data.pop("privacy_source_sha256", None) != POLICY_SOURCE_HASH:
            raise ValueError(f"Review {language} privacy translation against the current English app policy")
        PRIVACY[language] = data.pop("privacy")
    COPY[language] = data


ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "dual": '<rect x="3" y="5" width="14" height="11" rx="2"/><rect x="10" y="10" width="11" height="9" rx="2"/>',
    "video": '<rect x="3" y="5" width="13" height="14" rx="2"/><path d="m16 9 5-3v12l-5-3"/>',
    "save": '<path d="M12 3v12m-4-4 4 4 4-4M4 16v4h16v-4"/>',
    "lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    "user": '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
    "clean": '<path d="m5 12 4 4L19 6"/>',
    "menu": '<path d="M4 7h16M4 17h16"/>',
    "plus": '<path d="M12 4v16M4 12h16"/>'
}


def e(value):
    return html.escape(str(value), quote=True)


def nl(value):
    return e(value).replace("\n", "<br>")


def icon(name):
    return '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + '</svg>'


def url(language, page):
    folder = LANGUAGES[language]["path"]
    return ("/" + folder + "/" if folder else "/") + ("" if page == "home" else page + ".html")


def asset(name):
    return "/assets/" + name


def screenshot(language, shot, loading="lazy"):
    alt = COPY[language]["image_alt"][shot]
    source = LANGUAGES[language]["screenshots"]
    priority = ' fetchpriority="high"' if loading == "eager" else ''
    return f'<img src="{asset(source + "-" + shot + ".jpg")}" alt="{e(alt)}" width="1100" height="2390" loading="{loading}" decoding="async"{priority}>'


def phone(language, shot, css="", eager=False):
    return f'<div class="phone {css}">{screenshot(language, shot, "eager" if eager else "lazy")}</div>'


def primary_cta(t, css="button"):
    if CONFIG["appStoreURL"]:
        return f'<a class="{css}" href="{e(CONFIG["appStoreURL"])}" target="_blank" rel="noopener">{t["download"]}{icon("arrow")}</a>'
    return f'<span class="status-pill">{t["coming"]}</span>'


def header(language, page):
    t = COPY[language]
    links = ''.join(f'<a href="{url(language, key)}" class="{"active" if key == page else ""}"' + (' aria-current="page"' if key == page else '') + f'>{t["nav"][i]}</a>' for i, key in enumerate(["home", "support", "privacy"]))
    languages = ''.join(f'<a href="{url(code, page)}" lang="{code}" hreflang="{code}" data-language-link="{code}"' + (' aria-current="true"' if code == language else '') + f'>{e(info["name"])}</a>' for code, info in LANGUAGES.items())
    switch = f'<details class="language-picker"><summary aria-label="{e(t["language_label"])}: {e(LANGUAGES[language]["name"])}"><span>{e(LANGUAGES[language]["name"])}</span></summary><nav aria-label="{e(t["language_label"])}">{languages}</nav></details>'
    cta = f'<a class="nav-cta" href="{url(language, "support")}#devices">{t["devices"]}{icon("arrow")}</a>'
    return f'''<a class="skip-link" href="#main">{t['skip']}</a><header class="site-header"><div class="wrap header-row">
<a class="brand" href="{url(language, 'home')}" aria-label="CaptureBoth"><img src="{asset('app-icon.png')}" alt="" width="43" height="43">CaptureBoth</a>
<div class="header-controls"><nav class="desktop-nav" aria-label="{e(t['main_nav_label'])}">{links}{cta}</nav>{switch}
<details class="mobile-nav"><summary aria-label="{e(t['menu'])}">{icon('menu')}</summary><nav aria-label="{e(t['main_nav_label'])}">{links}</nav></details></div></div></header>'''


def footer(language):
    t = COPY[language]
    credit = e(t["publisher_label"].replace("Eastwood", CONFIG["brandPublisher"]))
    links = ''.join(f'<a href="{url(language, key)}">{t["nav"][i]}</a>' for i, key in enumerate(["home", "support", "privacy"]))
    return f'''<footer class="site-footer"><div class="wrap"><div class="footer-top"><a class="brand" href="{url(language,'home')}"><img src="{asset('app-icon.png')}" alt="" width="33" height="33">CaptureBoth</a><nav class="footer-links" aria-label="{e(t['footer_nav_label'])}">{links}</nav></div>
<div class="footer-bottom"><div class="copyright">© 2026 {e(POLICY['operatorName'])}. {t['rights']}<br>{credit} · <a href="mailto:{e(POLICY['contactEmail'])}">{e(POLICY['contactEmail'])}</a></div><div class="footer-note">{t['footer_tagline']}</div></div></div></footer>'''


def shell(language, page, body):
    t = COPY[language]
    description = t["description"] if page == "home" else t["support_intro"] if page == "support" else t["policy_intro"]
    title = "CaptureBoth — " + t["headline"] + " " + t["highlight"] if page == "home" else t["nav"][["home", "support", "privacy"].index(page)] + " · CaptureBoth"
    canonical = ""
    if CONFIG["siteURL"]:
        origin = CONFIG["siteURL"].rstrip("/")
        canonical = f'<link rel="canonical" href="{e(origin + url(language,page))}"><meta property="og:url" content="{e(origin + url(language,page))}"><meta property="og:image" content="{e(origin + asset("app-icon.png"))}">'
        canonical += ''.join(f'<link rel="alternate" hreflang="{lang}" href="{e(origin + url(lang,page))}">' for lang in COPY)
        canonical += f'<link rel="alternate" hreflang="x-default" href="{e(origin + url("en",page))}">'
    return f'''<!doctype html>
<html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#f6f3ed"><meta name="format-detection" content="telephone=no"><title>{e(title)}</title><meta name="description" content="{e(description)}"><meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">{canonical}<link rel="icon" type="image/png" href="{asset('favicon.png')}"><link rel="apple-touch-icon" href="{asset('app-icon.png')}"><link rel="stylesheet" href="{asset('style.css')}"><script src="{asset('site.js')}" defer></script></head>
<body>{header(language,page)}{body}{footer(language)}</body></html>'''


def home(language):
    t = COPY[language]
    promises = ''.join(f'<div>{icon(i)}<span>{text}</span></div>' for i, text in zip(["dual", "video", "save"], t["promises"]))
    moments = ''.join(f'<article class="moment"><div class="moment-label">{row[0]}</div><h3>{row[1]}</h3><p>{row[2]}</p>{phone(language,row[3])}<div class="moment-footer"><span>{t["sample"]}</span></div></article>' for row in t["moments"])
    tabs = ''.join(f'<button class="showcase-tab" id="tab-{row[2]}" role="tab" aria-controls="panel-{row[2]}" aria-selected="{"true" if index==0 else "false"}"><span class="tab-number">0{index+1}</span><span><strong>{row[0]}</strong><small>{row[1]}</small></span>{icon("arrow")}</button>' for index, row in enumerate(t["tabs"]))
    panels = ''.join(f'<figure role="tabpanel" id="panel-{row[2]}" aria-labelledby="tab-{row[2]}" tabindex="0">{phone(language,row[2])}<figcaption>{row[0]}<br>{t["illustrative"]}</figcaption></figure>' for row in t["tabs"])
    steps = ''.join(f'<article class="step"><span class="number">0{i+1}</span><h3>{row[0]}</h3><p>{row[1]}</p></article>' for i, row in enumerate(t["steps"]))
    points = ''.join(f'<li>{icon(name)}{text}</li>' for name, text in zip(["lock", "user", "clean"], t["privacy_points"]))
    return shell(language, "home", f'''<main id="main"><section class="wrap hero"><div class="hero-copy"><p class="eyebrow"><span class="dot"></span>{t['eyebrow']}</p><h1>{t['headline']}<br><span>{t['highlight']}</span></h1><p class="hero-intro">{t['intro']}</p><div class="hero-actions"><a class="button" href="#moments">{t['explore']}{icon('arrow')}</a><a class="text-link" href="{url(language,'support')}">{t['guide']}</a></div><div class="hero-meta">{''.join('<span>'+v+'</span>' for v in t['meta'])}</div></div>
<div class="hero-art"><div class="hero-halo" aria-hidden="true"></div>{phone(language,'travel','phone-main',True)}{phone(language,'record','phone-secondary',True)}<div class="lens-mark">{icon('dual')}{t['both']}</div><p class="art-note">{t['illustrative']}</p></div></section>
<div class="wrap promise-line">{promises}</div>
<section class="wrap" id="moments"><div class="section-head"><div><p class="eyebrow">{t['moments_eyebrow']}</p><h2>{nl(t['moments_title'])}</h2></div><p>{t['moments_intro']}</p></div><div class="moments-grid">{moments}</div></section>
<section class="wrap section-space showcase" data-showcase><div><p class="eyebrow">{t['showcase_eyebrow']}</p><h2>{nl(t['showcase_title'])}</h2><div class="showcase-tabs" role="tablist" aria-label="{t['tabs_label']}" aria-orientation="vertical">{tabs}</div></div><div class="showcase-stage">{panels}</div></section>
<section class="wrap simple-steps"><div class="steps-title"><h2>{t['steps_title']}</h2><a class="text-link" href="{url(language,'support')}">{t['all_help']}{icon('arrow')}</a></div><div class="steps-grid">{steps}</div></section>
<section class="wrap privacy-band"><div><p class="eyebrow">{t['privacy_eyebrow']}</p><h2>{nl(t['privacy_title'])}</h2><p>{t['privacy_intro']}</p><a class="text-link" href="{url(language,'privacy')}">{t['read_policy']}{icon('arrow')}</a></div><ul class="privacy-points">{points}</ul></section>
<section class="wrap final-cta"><div><h2>{t['final_title']}</h2><p>{t['final_intro']}</p></div>{primary_cta(t)}</section></main>''')


def support(language):
    t = COPY[language]
    quick = ''.join(f'<li><div><h3>{row[0]}</h3><p>{row[1]}</p></div></li>' for row in t["steps"])
    faq = ''.join(f'<details class="faq-item" id="{row[0]}"><summary>{row[1]}{icon("plus")}</summary><div class="faq-answer">{row[2]}</div></details>' for row in t["faq"])
    return shell(language, "support", f'''<main id="main" class="wrap"><header class="page-hero"><p class="eyebrow">CAPTUREBOTH / {e(t['nav'][1])}</p><h1>{nl(t['support_title'])}</h1><p>{t['support_intro']}</p></header><div class="help-layout"><div class="help-content"><h2>{t['quick_title']}</h2><ol class="quickstart">{quick}</ol><h2>{t['faq_title']}</h2><div class="faq-list">{faq}</div><section class="feedback-box"><h2>{t['feedback_title']}</h2><p>{t['feedback_intro']}</p><pre id="feedback-template">{e(t['feedback_template'])}</pre><button class="button" data-copy-feedback data-success="{e(t['copy_success'])}" data-failure="{e(t['copy_failure'])}">{t['copy']}{icon('arrow')}</button><p class="copy-status" id="copy-status" role="status" aria-live="polite"></p></section></div>
<aside class="help-aside"><section class="contact-box"><p class="eyebrow">{t['contact_eyebrow']}</p><h2>{t['contact_title']}</h2><p>{t['contact_intro']}</p><a class="email" href="mailto:{e(POLICY['contactEmail'])}">{e(POLICY['contactEmail'])}</a></section><div class="publisher"><strong>{t['publisher']}</strong>{e(POLICY['operatorName'])}<br><a class="text-link" href="{url(language,'privacy')}">{t['read_policy']}{icon('arrow')}</a></div></aside></div></main>''')


def privacy(language):
    t = COPY[language]
    content = PRIVACY[language]
    sections = ''.join(f'<section class="policy-section" id="policy-{i+1}"><h2>{e(row["title"])}</h2><p>{e(row["body"])}</p></section>' for i, row in enumerate(content["sections"]))
    toc = ''.join(f'<a href="#policy-{i+1}">{e(row["title"])}</a>' for i, row in enumerate(content["sections"]))
    toc += f'<a href="#policy-contact">{e(content["contactTitle"])}</a><a href="#website-privacy">{t["website_title"]}</a>'
    return shell(language, "privacy", f'''<main id="main" class="wrap"><header class="page-hero"><p class="eyebrow">CAPTUREBOTH / {e(t['nav'][2])}</p><h1>{nl(t['policy_title'])}</h1><p>{t['policy_intro']}</p><p class="page-meta">{t['updated']} · {e(POLICY['updated'])}</p></header><div class="policy-layout"><nav class="policy-toc" aria-label="{t['toc']}"><p class="eyebrow">{t['toc']}</p>{toc}</nav><article class="policy-document"><p class="policy-summary">{e(content['summary'])}</p>{sections}<section class="policy-section" id="policy-contact"><h2>{e(content['contactTitle'])}</h2><p class="legal-name">{e(POLICY['operatorName'])}</p><p>{e(content['contactFallback'])}</p><p><a href="mailto:{e(POLICY['contactEmail'])}">{e(POLICY['contactEmail'])}</a></p></section><section class="policy-section website-policy" id="website-privacy"><h2>{t['website_title']}</h2><p>{e(t['website_body'])}</p><p><a href="https://www.cloudflare.com/privacypolicy/" target="_blank" rel="noopener">{t['cloudflare_policy']}</a></p></section></article></div></main>''')


def main():
    if not POLICY["operatorName"] or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", POLICY["contactEmail"]):
        raise SystemExit("Provide the publisher name and a valid support email in PrivacyPolicy.json.")
    for key in ["siteURL", "appStoreURL"]:
        value = CONFIG[key]
        if value and (urlparse(value).scheme != "https" or not urlparse(value).netloc):
            raise SystemExit(f"{key} must be an actual HTTPS URL or empty")
    if CONFIG["siteURL"] and urlparse(CONFIG["siteURL"]).path not in ["", "/"]:
        raise SystemExit("siteURL must be the deployment origin, without a subdirectory")
    if set(COPY) != set(LANGUAGES):
        raise SystemExit("Every supported language needs a locale file")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "assets").mkdir()
    images = ["app-icon.png", "favicon.png"]
    images += [f'{source}-{shot}.jpg' for source in {info["screenshots"] for info in LANGUAGES.values()} for shot in ["travel", "record", "style", "preview", "light", "swap"]]
    for name in images:
        shutil.copyfile(HERE / "assets" / name, DIST / "assets" / name)
    for source in ["style.css", "site.js"]:
        shutil.copyfile(HERE / "src" / source, DIST / "assets" / source)
    for language in COPY:
        folder = DIST / LANGUAGES[language]["path"]
        folder.mkdir(exist_ok=True)
        for name, render in [("index.html", home), ("support.html", support), ("privacy.html", privacy)]:
            (folder / name).write_text(render(language))
    t = COPY["en"]
    (DIST / "404.html").write_text(shell("en", "home", f'<main id="main" class="wrap not-found"><p class="eyebrow">404 / OUT OF FRAME</p><h1>{t["missing_title"]}</h1><p>{t["missing_intro"]}</p><a class="button" href="/">{t["back_home"]}{icon("arrow")}</a></main>'))
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n" + ("Sitemap: " + CONFIG["siteURL"].rstrip("/") + "/sitemap.xml\n" if CONFIG["siteURL"] else ""))
    sitemap = DIST / "sitemap.xml"
    if CONFIG["siteURL"]:
        urls = [CONFIG["siteURL"].rstrip("/") + url(language, page) for language in COPY for page in ["home", "support", "privacy"]]
        sitemap.write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + e(u) + '</loc></url>' for u in urls) + '</urlset>')
    elif sitemap.exists():
        sitemap.unlink()
    (DIST / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: DENY\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-ancestors 'none'\n")
    redirects = ["/en/ / 301", "/en / 301", "/en/index.html / 301", "/zh-hans/ /zh-hant/ 301", "/zh-hans /zh-hant/ 301", "/zh-hans/index.html /zh-hant/ 301"]
    for page in ["privacy", "support"]:
        redirects += [f"/en/{page} /{page} 301", f"/en/{page}.html /{page} 301", f"/{page}-en.html /{page} 301", f"/{page}-zh-Hans.html /zh-hant/{page} 301", f"/zh-hans/{page} /zh-hant/{page} 301", f"/zh-hans/{page}.html /zh-hant/{page} 301"]
    (DIST / "_redirects").write_text("\n".join(redirects) + "\n")
    archive = ARCHIVE_PATH
    archive.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for file in sorted(DIST.rglob("*")):
            if file.is_file():
                output.write(file, file.relative_to(DIST))
    report = {"builtFor": "Cloudflare Pages static hosting", "date": CONFIG["websiteUpdated"], "pages": len(COPY) * 3, "defaultLanguage": "en", "languages": list(LANGUAGES), "publisher": POLICY["operatorName"], "supportEmail": POLICY["contactEmail"], "appStoreURLConfigured": bool(CONFIG["appStoreURL"]), "siteURLConfigured": bool(CONFIG["siteURL"]), "appPolicySHA256": hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest(), "published": False, "archive": str(archive.relative_to(PROJECT_ROOT)), "archiveBytes": archive.stat().st_size}
    (HERE / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
