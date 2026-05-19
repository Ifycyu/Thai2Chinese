"""URL validation utility to prevent SSRF attacks."""
import ipaddress
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


def validate_url(url: str) -> str | None:
    """Validate a URL for outbound requests. Returns error message if blocked, None if OK."""
    if not url:
        return None

    try:
        parsed = urlparse(url)
    except Exception:
        return "无效的URL格式"

    if parsed.scheme not in ("http", "https"):
        return "只允许 http 和 https 协议"

    hostname = parsed.hostname
    if not hostname:
        return "URL缺少主机名"

    if hostname.lower() in BLOCKED_HOSTS:
        return f"不允许访问主机: {hostname}"

    try:
        ip = ipaddress.ip_address(hostname)
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return f"不允许访问内部IP地址: {hostname}"
    except ValueError:
        # hostname is a domain name, check DNS resolution
        try:
            infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in infos:
                resolved_ip = ipaddress.ip_address(sockaddr[0])
                for network in BLOCKED_NETWORKS:
                    if resolved_ip in network:
                        return f"域名解析到内部IP地址: {hostname} -> {resolved_ip}"
        except socket.gaierror:
            return f"无法解析域名: {hostname}"

    return None
