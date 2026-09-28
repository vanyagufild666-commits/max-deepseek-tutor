import ssl

try:
    import truststore
except ImportError:  # fallback if dependencies were not refreshed yet
    truststore = None


def create_ssl_context() -> ssl.SSLContext:
    """
    Use the operating system certificate store when truststore is available.
    This is especially important on Windows, where antivirus/proxy root
    certificates may exist in the Windows trust store but not in certifi.
    """
    if truststore is not None:
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    return ssl.create_default_context()
