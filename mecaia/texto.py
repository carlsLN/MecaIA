import re
import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples, para comparar texto."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes.lower()).strip()
