from extensions import db


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    categoria = db.Column(db.String(80))
    precio = db.Column(db.Float, nullable=False, default=0)
    imagen = db.Column(db.String(250), default="default.png")

    # PRODUCTO_LISTO o PRODUCTO_PERSONALIZADO
    tipo = db.Column(db.String(30), nullable=False, default="PRODUCTO_LISTO")

    # Solo aplica de verdad a PRODUCTO_LISTO; personalizados se fabrican bajo pedido
    stock = db.Column(db.Integer, default=0)

    # ACTIVO / INACTIVO (baja lógica, nunca se elimina físicamente)
    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")

    horas_estimadas = db.Column(db.Float, default=0)  # para cálculo de capacidad de producción

    receta = db.relationship("RecetaInsumo", backref="producto", lazy=True,
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Producto {self.nombre} ({self.tipo})>"


class Insumo(db.Model):
    __tablename__ = "insumos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    unidad = db.Column(db.String(20), nullable=False)  # UNIDAD, METRO, LITRO, KILOGRAMO
    stock_actual = db.Column(db.Float, nullable=False, default=0)
    stock_minimo = db.Column(db.Float, nullable=False, default=0)
    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")

    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo

    def __repr__(self):
        return f"<Insumo {self.nombre}>"


class RecetaInsumo(db.Model):
    """Relaciona un producto con los insumos y cantidades necesarias por unidad."""
    __tablename__ = "receta_insumos"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    insumo_id = db.Column(db.Integer, db.ForeignKey("insumos.id"), nullable=False)
    cantidad_por_unidad = db.Column(db.Float, nullable=False)  # ej: 1.5 metros por mochila

    insumo = db.relationship("Insumo")


class Alerta(db.Model):
    __tablename__ = "alertas"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(30), nullable=False)  # STOCK_BAJO, etc.
    mensaje = db.Column(db.String(300), nullable=False)
    insumo_id = db.Column(db.Integer, db.ForeignKey("insumos.id"))
    fecha = db.Column(db.DateTime)
    atendida = db.Column(db.Boolean, default=False)
