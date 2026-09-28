from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False, index=True)
    telefono = db.Column(db.String(30))
    direccion = db.Column(db.String(250))
    password_hash = db.Column(db.String(255), nullable=False)

    # Rol: CLIENTE, EMPLEADO, DUENO -- se obtiene siempre desde la sesión
    # autenticada en backend, nunca desde el navegador.
    rol = db.Column(db.String(20), nullable=False, default="CLIENTE")

    # ACTIVO / INACTIVO. Los empleados desactivados no pueden iniciar sesión.
    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")

    horas_disponibles = db.Column(db.Float, default=0)  # solo relevante para EMPLEADO

    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    correo_verificado = db.Column(db.Boolean, default=False)

    pedidos = db.relationship("Pedido", backref="cliente", lazy=True,
                               foreign_keys="Pedido.usuario_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        # Requerido por Flask-Login: bloquea el login de usuarios INACTIVOS.
        return self.estado == "ACTIVO"

    def __repr__(self):
        return f"<Usuario {self.correo} ({self.rol})>"
