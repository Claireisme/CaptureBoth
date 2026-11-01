#!/usr/bin/env python3
"""Verify rendered pages, policy provenance, internal links and upload archive."""
import json
import html
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from build import COPY, LANGUAGES, PRIVACY, CONFIG, POLICY_PATH, ARCHIVE_PATH, shell, url

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = HERE / "dist"


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links, self.ids, self.h1s, self.lang, self.images = [], [], 0, None, []
        self.language_links = {}
        self.anchors = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            assert values["id"] not in self.ids, "Duplicate element ID: " + values["id"]
            self.ids.append(values["id"])
        if tag == "h1": self.h1s += 1
        if tag == "html": self.lang = values.get("lang")
        if "data-language-link" in values:
            code = values["data-language-link"]
            assert code not in self.language_links
            assert values.get("lang") == code and values.get("hreflang") == code
            self.language_links[code] = values["href"]
        for attr in ["href", "src"]:
            if attr in values: self.links.append(values[attr])
        if tag == "a": self.anchors.append(values)
        if tag == "img":
            assert all(key in values for key in ["alt", "width", "height"]), "Image needs alt and dimensions"
            self.images.append(values)


def resolve(path):
    item = DIST / path.lstrip("/")
    if item.is_dir(): return item / "index.html"
    if item.is_file(): return item
    if not item.suffix: return item.with_suffix(".html")
    return item


def main():
    def schema(value):
        if isinstance(value, dict): return {key: schema(item) for key, item in value.items()}
        if isinstance(value, list): return [schema(item) for item in value]
        assert isinstance(value, str) and value.strip(), "Every translation must be nonempty text"
        return "text"
    for lang in LANGUAGES:
        assert schema(COPY[lang]) == schema(COPY["en"]), (lang, "Incomplete website translation")
        assert schema(PRIVACY[lang]) == schema(PRIVACY["en"]), (lang, "Incomplete policy translation")
        for key in ["faq", "moments", "tabs"]:
            index = 0 if key == "faq" else -1
            assert [row[index] for row in COPY[lang][key]] == [row[index] for row in COPY["en"][key]]
    parsed = {}
    for file in sorted(DIST.rglob("*.html")):
        source = file.read_text()
        page = Page(source)
        assert page.h1s == 1 and page.lang in LANGUAGES, file
        assert 'mailto:CaptureBoth@520.ie' in source
        assert "Eastwood Management Services Limited" in source
        assert "<form" not in source and "<iframe" not in source
        section = "home" if file.name in ["index.html", "404.html"] else file.stem
        assert page.language_links == {code: url(code, section) for code in LANGUAGES}, file
        parsed[file] = page
    expected = {resolve(url(lang, page)) for lang in LANGUAGES for page in ["home", "support", "privacy"]} | {DIST / "404.html"}
    assert set(parsed) == expected and parsed[DIST / "index.html"].lang == "en"
    assert parsed[DIST / "404.html"].lang == "en"
    for file, page in parsed.items():
        for link in page.links:
            parts = urlsplit(link)
            assert link != "#", (file, "Empty destination")
            if parts.scheme:
                assert parts.scheme in ["https", "mailto"], (file, link)
                continue
            if parts.path:
                target = resolve(parts.path) if parts.path.startswith("/") else file.parent / parts.path
                assert target.is_file(), (file, link)
            else:
                target = file
            if parts.fragment:
                assert target in parsed and unquote(parts.fragment) in parsed[target].ids, (file, link)
    if CONFIG["appStoreURL"]:
        for lang in LANGUAGES:
            file = resolve(url(lang, "home"))
            source = file.read_text()
            store_links = [a for a in parsed[file].anchors if a.get("href") == CONFIG["appStoreURL"]]
            assert len(store_links) >= 4, (file, "Missing App Store download entry")
            assert all(a.get("target") == "_blank" and "noopener" in a.get("rel", "").split() for a in store_links)
            assert html.escape(COPY[lang]["coming"]) not in source, (file, "Stale launch status")
    policy = json.loads(POLICY_PATH.read_text())
    for lang, content in PRIVACY.items():
        file = resolve(url(lang, "privacy"))
        source = file.read_text()
        for section in content["sections"]:
            assert html.escape(section["title"], quote=True) in source
            assert html.escape(section["body"], quote=True) in source
        assert policy["updated"] in source and html.escape(content["contactTitle"], quote=True) in source
    for line in (DIST / "_redirects").read_text().splitlines():
        origin, destination, status = line.split()
        assert status == "301" and origin != destination and resolve(destination).is_file(), line
    configured = CONFIG["siteURL"]
    try:
        CONFIG["siteURL"] = "https://captureboth.example"
        rendered = shell("fr", "support", "<main></main>")
        assert 'hreflang="x-default" href="https://captureboth.example/support.html"' in rendered
        for code in LANGUAGES:
            assert f'hreflang="{code}" href="https://captureboth.example{url(code, "support")}"' in rendered
    finally:
        CONFIG["siteURL"] = configured
    script = (DIST / "assets/site.js").read_text()
    assert not re.search(r"\b(fetch|XMLHttpRequest|localStorage|sessionStorage)\b|document\.cookie", script)
    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        assert archive.testzip() is None
        assert "index.html" in archive.namelist() and "_headers" in archive.namelist()
        assert not any(name.startswith("dist/") or ".." in Path(name).parts for name in archive.namelist())
        assert set(archive.namelist()) == {str(file.relative_to(DIST)) for file in DIST.rglob("*") if file.is_file()}
        for file in DIST.rglob("*"):
            if file.is_file(): assert archive.read(str(file.relative_to(DIST))) == file.read_bytes()
    report = {"htmlPages": len(parsed), "defaultLanguage": "en", "languages": list(LANGUAGES), "completeTranslations": "passed", "internalLinksAndAnchors": "passed", "languageSwitchDestinations": "passed", "legacyRedirects": "passed", "hreflangAndDefault": "passed", "appPrivacySource": "matched", "archive": "passed", "thirdPartyScriptsOrForms": False}
    (HERE / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
