from datetime import datetime
from extensions import db

ESTADOS_PEDIDO = [
    "PENDIENTE", "ACEPTADO", "RECHAZADO", "EN_PRODUCCION",
    "TERMINADO", "ENTREGADO", "CANCELADO",
]

# Transiciones válidas controladas por el backend (sección 14)
TRANSICIONES_VALIDAS = {
    "PENDIENTE": {"ACEPTADO", "RECHAZADO", "CANCELADO"},
    "ACEPTADO": {"EN_PRODUCCION", "CANCELADO"},
    "EN_PRODUCCION": {"TERMINADO", "CANCELADO"},
    "TERMINADO": {"ENTREGADO"},
    "RECHAZADO": set(),
    "ENTREGADO": set(),
    "CANCELADO": set(),
}


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    tipo = db.Column(db.String(30), nullable=False, default="LISTO")  # LISTO o PERSONALIZADO
    estado = db.Column(db.String(30), nullable=False, default="PENDIENTE")

    total = db.Column(db.Float, default=0)
    anticipo = db.Column(db.Float, default=0)

    # Solo para personalizados con insumos insuficientes al momento de solicitar
    revision_stock = db.Column(db.Boolean, default=False)
    motivo_rechazo = db.Column(db.String(300))

    detalles = db.relationship("DetallePedido", backref="pedido", lazy=True,
                                cascade="all, delete-orphan")
    personalizacion = db.relationship("Personalizacion", backref="pedido", uselist=False,
                                       cascade="all, delete-orphan")
    pagos = db.relationship("Pago", backref="pedido", lazy=True)
    produccion = db.relationship("Produccion", backref="pedido", uselist=False,
                                  cascade="all, delete-orphan")

    @property
    def saldo_pendiente(self):
        return round(self.total - self.anticipo, 2)

    def puede_transicionar_a(self, nuevo_estado):
        return nuevo_estado in TRANSICIONES_VALIDAS.get(self.estado, set())


class DetallePedido(db.Model):
    __tablename__ = "detalle_pedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    producto = db.relationship("Producto")

    @property
    def subtotal(self):
        return round(self.cantidad * self.precio_unitario, 2)


class Personalizacion(db.Model):
    __tablename__ = "personalizaciones"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)

    # Atributos dinámicos de personalización guardados como texto "clave: valor"
    atributos_json = db.Column(db.Text)  # JSON serializado
    descripcion_adicional = db.Column(db.Text)

    producto = db.relationship("Producto")


class Pago(db.Model):
    __tablename__ = "pagos"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(20), nullable=False)  # EFECTIVO, QR, TARJETA
    estado = db.Column(db.String(20), nullable=False)  # APROBADO, RECHAZADO
    transaction_id = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    cliente_nombre = db.Column(db.String(150))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    metodo_pago = db.Column(db.String(20), nullable=False)
    total = db.Column(db.Float, default=0)

    empleado = db.relationship("Usuario")
    detalles = db.relationship("DetalleVenta", backref="venta", lazy=True,
                                cascade="all, delete-orphan")


class DetalleVenta(db.Model):
    __tablename__ = "detalle_venta"

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    producto = db.relationship("Producto")


class Produccion(db.Model):
    __tablename__ = "produccion"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_limite = db.Column(db.Date)
    horas_estimadas = db.Column(db.Float, default=0)
    estado = db.Column(db.String(20), default="PENDIENTE")  # PENDIENTE, EN_PROCESO, TERMINADO

    empleado = db.relationship("Usuario")
