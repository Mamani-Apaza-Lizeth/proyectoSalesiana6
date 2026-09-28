"""
Servicio de inventario (secciones 12, 13, 24).

Reglas clave:
- La cantidad solicitada del producto NUNCA se interpreta como cantidad de
  materiales: los materiales se calculan multiplicando la receta por la
  cantidad pedida.
- El stock se valida siempre en el backend, nunca solo en el frontend.
- Cuando stock_actual <= stock_minimo se genera una alerta (y un correo).
"""
from datetime import datetime
from extensions import db
from models import Alerta
from services.correo import enviar_alerta_stock_bajo


def calcular_materiales_requeridos(producto, cantidad):
    """Devuelve una lista de dicts: insumo, cantidad_necesaria, disponible, suficiente."""
    resultado = []
    for r in producto.receta:
        cantidad_necesaria = r.cantidad_por_unidad * cantidad
        resultado.append({
            "insumo": r.insumo,
            "cantidad_necesaria": round(cantidad_necesaria, 3),
            "disponible": r.insumo.stock_actual,
            "suficiente": r.insumo.stock_actual >= cantidad_necesaria,
        })
    return resultado


def materiales_suficientes(producto, cantidad):
    materiales = calcular_materiales_requeridos(producto, cantidad)
    if not materiales:
        return True  # producto sin receta definida: no se bloquea
    return all(m["suficiente"] for m in materiales)


def descontar_insumos(producto, cantidad):
    """Descuenta del inventario los insumos usados y genera alertas si corresponde."""
    for r in producto.receta:
        insumo = r.insumo
        insumo.stock_actual = max(0, insumo.stock_actual - (r.cantidad_por_unidad * cantidad))
        db.session.flush()
        verificar_alerta_stock(insumo)


def verificar_alerta_stock(insumo):
    """Genera una alerta (y correo) SOLO cuando el cambio lleva el stock al límite o por debajo."""
    if insumo.stock_bajo():
        ya_existe = Alerta.query.filter_by(
            insumo_id=insumo.id, tipo="STOCK_BAJO", atendida=False
        ).first()
        if not ya_existe:
            alerta = Alerta(
                tipo="STOCK_BAJO",
                mensaje=f"El insumo '{insumo.nombre}' tiene stock bajo "
                        f"({insumo.stock_actual} {insumo.unidad} disponibles, "
                        f"mínimo {insumo.stock_minimo}).",
                insumo_id=insumo.id,
                fecha=datetime.utcnow(),
            )
            db.session.add(alerta)
            db.session.flush()
            enviar_alerta_stock_bajo(insumo)
    else:
        # El stock volvió a subir por encima del mínimo: se marcan atendidas las alertas abiertas
        Alerta.query.filter_by(insumo_id=insumo.id, tipo="STOCK_BAJO", atendida=False) \
            .update({"atendida": True})


def validar_stock_producto_listo(producto, cantidad):
    """Sección 10/17: verificación de stock de productos listos antes de vender."""
    return producto.estado == "ACTIVO" and producto.stock >= cantidad and cantidad > 0
