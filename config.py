import os
from pathlib import Path

from dotenv import load_dotenv

# Muat variabel environment dari  .env jika ada
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")


class Config:
    """konfigurasi dasar aplikasi."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    @staticmethod
    def init_app(app):
        # Validasi rahasia aplikasi di luar testing (NF-10)
        if not app.testing and not app.config.get("SECRET_KEY"):
            raise ValueError(
                "SECRET_KEY wajib diatur di dalam berkas.env sebelum menjalankan aplikasi!"
            )


class DevelopmentConfig(Config):
    """Konfigurasi untuk pengembangan lokal."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{basedir / 'instance' / 'pos_smk.db'}"
    )


class TestingConfig(Config):
    """Konfigurasi untuk pengujian otomatis (pytest)."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "testing-secret-key-for-automated-tests"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Konfigurasi utuk dijalankan di LAN lab tanpa debug."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{basedir / 'instance' / 'pos_smk.db'}"
    )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
