"""URL validation utility to prevent SSRF attacks (with DNS rebinding protection)."""
import ipaddress
import os
import socket
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

BLOCKED_HOSTS = {"localhost", "metadata.google.internal", "instance-data"}

# Allowed dictionary API domains (whitelist)
DICT_API_ALLOWED_DOMAINS = os.environ.get(
    "DICT_API_ALLOWED_DOMAINS", "xcxapi.seak.online"
).split(",")


def _is_blocked_ip(ip_str: str) -> bool:
    """Check if an IP address is in a blocked network."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return True
    except ValueError:
        pass
    return False


def validate_url(url: str) -> tuple[str, str | None]:
    """Validate a URL for outbound requests.

    Returns (resolved_ip, error_message).
    If valid: (resolved_ip, None)
    If blocked: ("", error_message)
    If empty: ("", None)
    """
    if not url:
        return "", None

    try:
        parsed = urlparse(url)
    except Exception:
        return "", "无效的URL格式"

    if parsed.scheme not in ("http", "https"):
        return "", "只允许 http 和 https 协议"

    hostname = parsed.hostname
    if not hostname:
        return "", "URL缺少主机名"

    if hostname.lower() in BLOCKED_HOSTS:
        return "", f"不允许访问主机: {hostname}"

    # Direct IP
    try:
        ip = ipaddress.ip_address(hostname)
        if _is_blocked_ip(str(ip)):
            return "", f"不允许访问内部IP地址: {hostname}"
        return str(ip), None
    except ValueError:
        pass

    # Domain name — resolve once and return the IP
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in infos:
            resolved_ip = sockaddr[0]
            if _is_blocked_ip(resolved_ip):
                return "", f"域名解析到内部IP地址: {hostname} -> {resolved_ip}"
        # Return first resolved IP (all checked safe)
        return infos[0][4][0], None
    except socket.gaierror:
        return "", f"无法解析域名: {hostname}"


def validate_dict_api_url(url: str) -> tuple[str, str | None]:
    """Validate dictionary API URL against domain whitelist, then SSRF checks.

    Returns (resolved_ip, error_message).
    """
    if not url:
        return "", None

    try:
        parsed = urlparse(url)
    except Exception:
        return "", "无效的URL格式"

    hostname = (parsed.hostname or "").lower()
    if hostname not in DICT_API_ALLOWED_DOMAINS:
        return "", f"词典API域名不允许: {hostname}，只允许: {', '.join(DICT_API_ALLOWED_DOMAINS)}"

    return validate_url(url)


def build_url_with_ip(url: str, resolved_ip: str) -> tuple[str, str]:
    """Replace hostname in URL with resolved IP. Returns (new_url, original_host)."""
    parsed = urlparse(url)
    original_host = parsed.hostname
    # Replace hostname with IP in netloc
    port = parsed.port
    if port:
        netloc = f"{resolved_ip}:{port}"
    else:
        netloc = resolved_ip
    new_url = parsed._replace(netloc=netloc).geturl()
    return new_url, original_host
