from urllib.parse import urlparse

def extract_plain_hostname(raw_host: str) -> str:
    """
    Extracts the plain hostname from a raw host string which may include schemes like https://
    or trailing slashes, ports, or paths.

    Examples:
    - https://mydb.example.com/ -> mydb.example.com
    - http://mydb.example.com:5432/path -> mydb.example.com
    - mydb.example.com/ -> mydb.example.com
    - mydb.example.com:5432 -> mydb.example.com
    """
    # Add a fake scheme if missing to make it parsable
    if "://" not in raw_host:
        raw_host = "http://" + raw_host

    parsed = urlparse(raw_host)
    hostname = parsed.hostname

    if hostname:
        return hostname.strip()
    else:
        raise ValueError(f"Could not extract a valid hostname from input: {raw_host}")
