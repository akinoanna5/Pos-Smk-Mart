import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_login import current_user

from app.cli import register_commands
from app.extensions import csrf, db, login_manager
from config import config


def create_app(config_name=None):
    """Application factory untuk pos-flask-smk"""
    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "default")

    app = Flask(__name__, instance_relative_config=True)
    config_class = config.get(config_name, config["default"])
    app.config.from_object(config_class)

    # pastikan direktori instance ada untuk database SQLite
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # inisialisasi konfigurasi khusus (misalnya validasi SECRET_KEY)
    config_class.init_app(app)

    # inisialisasi ekstensi
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # User loader untuk Flask-Login: memuat user dari ID yang tersimpan di sesi
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Daftarkan perintah CLI (flask init-db, flask seed)
    register_commands(app)

    # Jinja2 filter: Rupiah dan waktu WIB
    @app.template_filter("rupiah")
    def rupiah_filter(value):
        """Memformat integer menjadi format rupiah Indonesia: Rp 12.500."""
        if value is None:
            return "Rp 0"
        try:
            val = int(value)
            formatted = f"{val:,}".replace(",", ".")
            return f"Rp {formatted}"
        except (ValueError, TypeError):
            return "Rp 0"

    @app.template_filter("waktu_wib")
    def waktu_wib_filter(value, format_str="%d/%m/%Y %H:%M"):
        """Mengonversi waktu UTC ke WIB (UTC+7) dan memformatnya."""
        if not value:
            return "-"
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            wib_tz = timezone(timedelta(hours=7))
            wib_time = value.astimezone(wib_tz)
            return wib_time.strftime(format_str)
        return str(value)

    # Penanganan error: halaman yang ramah, tanpa jejak kesalahan (traceback)
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Rute root '/': arahkan sesuai status login dan peran
    @app.route("/")
    def root():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for("dashboard.index"))
            return redirect(url_for("pos.index"))
        return redirect(url_for("auth.login"))

    # Daftarkan blueprint
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.dashboard import bp as dashboard_bp
    from app.blueprints.laporan import bp as laporan_bp
    from app.blueprints.metode_bayar import bp as metode_bayar_bp
    from app.blueprints.order import bp as order_bp
    from app.blueprints.pelanggan import bp as pelanggan_bp
    from app.blueprints.pengaturan import bp as pengaturan_bp
    from app.blueprints.pengguna import bp as pengguna_bp
    from app.blueprints.pos import bp as pos_bp
    from app.blueprints.produk import bp as produk_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pengguna_bp)
    app.register_blueprint(produk_bp)
    app.register_blueprint(pelanggan_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(metode_bayar_bp)
    app.register_blueprint(pengaturan_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(laporan_bp)

    return app
