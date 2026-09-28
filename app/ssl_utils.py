import os
import ssl
from pathlib import Path

try:
    import truststore
except ImportError:
    truststore = None


def create_ssl_context() -> ssl.SSLContext:
    """
    Prefer an explicitly configured CA bundle (used on Bothost for
    standard CAs + Russian Trusted CA). Otherwise use the native OS
    certificate store on Windows/macOS when truststore is available.
    """
    ca_file = os.getenv("SSL_CERT_FILE")
    if ca_file and Path(ca_file).is_file():
        return ssl.create_default_context(cafile=ca_file)

    if truststore is not None:
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    return ssl.create_default_context()
