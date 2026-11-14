import ipaddress
import socket
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag, urlunparse

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "BugLens/1.0 (educational website quality scanner)"
TIMEOUT = httpx.Timeout(8.0, connect=5.0)
MAX_BYTES = 1_500_000

def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValueError("Please enter a website URL.")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only public HTTP or HTTPS website URLs are supported.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing usernames or passwords are not supported.")
    if not _public_host(parsed.hostname):
        raise ValueError("This scanner only accepts public internet hostnames.")
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, ""))

def _public_host(host: str) -> bool:
    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            addresses = {ipaddress.ip_address(info[4][0]) for info in infos}
        except socket.gaierror:
            return False
    return bool(addresses) and all(ip.is_global for ip in addresses)

def _fetch(client: httpx.Client, url: str):
    # Validate every target, including discovered links and redirect destinations.
    if not _public_host(urlparse(url).hostname or ""):
        return None, "Blocked non-public host"
    try:
        with client.stream("GET", url, follow_redirects=False) as response:
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    return response.status_code, "Redirect without a location"
                target = urljoin(url, location)
                if not _public_host(urlparse(target).hostname or ""):
                    return response.status_code, "Blocked redirect to non-public host"
                return response.status_code, "Redirect: " + target
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                return response.status_code, "Not an HTML page"
            chunks, size = [], 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > MAX_BYTES:
                    return response.status_code, "Page exceeded the 1.5 MB scan limit"
                chunks.append(chunk)
            return response.status_code, b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
    except httpx.TimeoutException:
        return None, "Request timed out"
    except httpx.RequestError:
        return None, "Request failed"

def scan_website(raw_url: str, max_pages: int = 10):
    start = normalize_url(raw_url)
    parsed_start = urlparse(start)
    origin = (parsed_start.scheme, parsed_start.netloc)
    queue = deque([start])
    visited = set()
    pages = []
    findings = []

    with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        while queue and len(visited) < max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            status, body = _fetch(client, url)
            page = {"url": url, "status_code": status, "title": "", "links_checked": 0}
            if not isinstance(body, str):
                page["note"] = body
                if status is None or (status and status >= 400):
                    findings.append(_finding("page_response", "high", url, str(body), "Check that the page is reachable and returns a successful response."))
                pages.append(page)
                continue

            soup = BeautifulSoup(body, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            description = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
            description_text = description.get("content", "").strip() if description else ""
            page["title"] = title
            if status and status >= 400:
                findings.append(_finding("page_response", "high", url, f"HTTP status {status}", "Check the page route and server response."))
            if not title:
                findings.append(_finding("missing_title", "medium", url, "No non-empty <title> element found.", "Add a concise, descriptive page title."))
            if not description_text:
                findings.append(_finding("missing_meta_description", "low", url, "Meta description is missing or empty.", "Add a short summary in a meta description tag."))
            for img in soup.find_all("img"):
                if not img.has_attr("alt"):
                    findings.append(_finding("missing_image_alt", "medium", url, str(img.get("src", "(image source unavailable)"))[:180], "Add an alt attribute. Use empty alt text for purely decorative images."))
            for link in soup.find_all("a", href=True):
                absolute = urldefrag(urljoin(url, link["href"]))[0]
                p = urlparse(absolute)
                if p.scheme not in ("http", "https") or (p.scheme, p.netloc) != origin:
                    continue
                if absolute not in visited and absolute not in queue and len(visited) + len(queue) < max_pages:
                    queue.append(absolute)
            page["links_checked"] = len(soup.find_all("a", href=True))
            pages.append(page)

    return {
        "scanned_url": start,
        "pages_scanned": len(pages),
        "findings_count": len(findings),
        "findings": findings,
        "pages": pages,
        "notice": "First-pass checks only. Results can be incomplete; timeouts and blocked requests are not proof of a broken page."
    }

def _finding(category, severity, url, evidence, fix):
    return {"category": category, "severity": severity, "url": url, "evidence": evidence, "suggested_fix": fix}
