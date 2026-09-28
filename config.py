import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "miraliz-dev-secret-cambiar-en-produccion")

    # SQLite durante el desarrollo. Para migrar a MySQL, solo se necesita
    # cambiar SQLALCHEMY_DATABASE_URI (ej. "mysql+pymysql://user:pass@host/db")
    # ya que todo el acceso a datos se hace a través de SQLAlchemy ORM.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "database", "miraliz.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Correo (modo desarrollo: si no hay credenciales, solo se imprime en consola)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DUENO = os.environ.get("MAIL_DUENO", "dueno@miraliz.com")
    CORREO_MODO_DESARROLLO = os.environ.get("MAIL_USERNAME", "") == ""
