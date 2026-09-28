import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user

from extensions import db
from models import Producto, Pedido, DetallePedido, Personalizacion
from routes.decorators import rol_requerido
from services.inventario import (
    validar_stock_producto_listo, calcular_materiales_requeridos,
    materiales_suficientes, descontar_insumos,
)

bp = Blueprint("cliente", __name__, url_prefix="/cliente")

CARRITO_SESSION_KEY = "carrito"


def _get_carrito():
    return session.setdefault(CARRITO_SESSION_KEY, {})


@bp.route("/panel")
@login_required
@rol_requerido("CLIENTE")
def dashboard():
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id) \
        .order_by(Pedido.fecha.desc()).limit(5).all()
    return render_template("cliente/panel.html", pedidos=pedidos)


# ---------------------------------------------------------------- CARRITO --

@bp.route("/carrito/agregar/<int:producto_id>", methods=["POST"])
@login_required
@rol_requerido("CLIENTE")
def agregar_carrito(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if producto.tipo != "PRODUCTO_LISTO":
        flash("Ese producto requiere una solicitud de personalización.", "warning")
        return redirect(url_for("cliente.personalizar", producto_id=producto_id))

    cantidad = int(request.form.get("cantidad", 1))
    carrito = _get_carrito()
    carrito[str(producto_id)] = carrito.get(str(producto_id), 0) + max(1, cantidad)
    session.modified = True

    flash(f"{producto.nombre} agregado al carrito.", "success")
    return redirect(request.referrer or url_for("public.catalogo"))


@bp.route("/carrito")
@login_required
@rol_requerido("CLIENTE")
def ver_carrito():
    carrito = _get_carrito()
    items, total = [], 0
    for pid, cantidad in carrito.items():
        producto = Producto.query.get(int(pid))
        if not producto:
            continue
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({"producto": producto, "cantidad": cantidad, "subtotal": subtotal})
    return render_template("cliente/carrito.html", items=items, total=total)


@bp.route("/carrito/actualizar/<int:producto_id>", methods=["POST"])
@login_required
@rol_requerido("CLIENTE")
def actualizar_carrito(producto_id):
    cantidad = int(request.form.get("cantidad", 1))
    carrito = _get_carrito()
    if cantidad <= 0:
        carrito.pop(str(producto_id), None)
    else:
        carrito[str(producto_id)] = cantidad
    session.modified = True
    return redirect(url_for("cliente.ver_carrito"))


@bp.route("/carrito/eliminar/<int:producto_id>", methods=["POST"])
@login_required
@rol_requerido("CLIENTE")
def eliminar_carrito(producto_id):
    carrito = _get_carrito()
    carrito.pop(str(producto_id), None)
    session.modified = True
    return redirect(url_for("cliente.ver_carrito"))


@bp.route("/carrito/confirmar", methods=["POST"])
@login_required
@rol_requerido("CLIENTE")
def confirmar_pedido():
    """Crea el pedido de productos LISTOS. Vuelve a validar stock en backend
    (nunca confía únicamente en lo mostrado en el navegador)."""
    carrito = _get_carrito()
    if not carrito:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for("cliente.ver_carrito"))

    errores = []
    items_validos = []
    for pid, cantidad in carrito.items():
        producto = Producto.query.get(int(pid))
        if not producto or not validar_stock_producto_listo(producto, cantidad):
            errores.append(f"Stock insuficiente para '{producto.nombre if producto else pid}'.")
        else:
            items_validos.append((producto, cantidad))

    if errores:
        for e in errores:
            flash(e, "danger")
        return redirect(url_for("cliente.ver_carrito"))

    pedido = Pedido(usuario_id=current_user.id, tipo="LISTO", estado="PENDIENTE")
    total = 0
    for producto, cantidad in items_validos:
        detalle = DetallePedido(producto_id=producto.id, cantidad=cantidad,
                                 precio_unitario=producto.precio)
        pedido.detalles.append(detalle)
        producto.stock -= cantidad  # descuento de stock al confirmar
        total += producto.precio * cantidad
    pedido.total = total

    db.session.add(pedido)
    db.session.commit()

    session[CARRITO_SESSION_KEY] = {}
    flash("Pedido creado. Continúa con el pago.", "success")
    return redirect(url_for("cliente.pagar_pedido", pedido_id=pedido.id))


# ---------------------------------------------------------- PERSONALIZADOS --

TEMAS_PREDEFINIDOS = ["Frozen", "Superhéroes", "Unicornios", "Fútbol", "Princesas", "Otro"]

CAMPOS_POR_PRODUCTO = {
    "Mochila": ["material", "material_interior", "acabado", "tematica"],
    "Piñata 2D": ["tematica", "tamano"],
}


@bp.route("/personalizar/<int:producto_id>", methods=["GET", "POST"])
@login_required
@rol_requerido("CLIENTE")
def personalizar(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if producto.tipo != "PRODUCTO_PERSONALIZADO":
        return redirect(url_for("public.detalle_producto", producto_id=producto_id))

    if request.method == "POST":
        cantidad = max(1, int(request.form.get("cantidad", 1)))
        tematica = request.form.get("tematica", "")
        if tematica == "Otro":
            tematica = request.form.get("tematica_otro", "Personalizada")

        atributos = {
            "material": request.form.get("material", ""),
            "material_interior": request.form.get("material_interior", ""),
            "acabado": request.form.get("acabado", "Estándar"),
            "tematica": tematica,
            "tamano": request.form.get("tamano", ""),
        }
        descripcion_adicional = request.form.get("descripcion_adicional", "")

        # Sección 12 y 13: cálculo de materiales y validación de stock
        suficiente = materiales_suficientes(producto, cantidad)

        pedido = Pedido(
            usuario_id=current_user.id, tipo="PERSONALIZADO", estado="PENDIENTE",
            total=producto.precio * cantidad,  # precio base (sección 16)
            revision_stock=not suficiente,
        )
        personalizacion = Personalizacion(
            producto_id=producto.id, cantidad=cantidad,
            atributos_json=json.dumps(atributos, ensure_ascii=False),
            descripcion_adicional=descripcion_adicional,
        )
        pedido.personalizacion = personalizacion

        db.session.add(pedido)
        db.session.commit()

        if suficiente:
            flash("✓ Los materiales requeridos están disponibles. "
                  "Tu solicitud fue enviada para revisión.", "success")
        else:
            flash("⚠ Algunos materiales no tienen stock suficiente. "
                  "Tu pedido quedará sujeto a revisión por parte de administración.", "warning")

        return redirect(url_for("cliente.dashboard"))

    materiales_preview = calcular_materiales_requeridos(producto, 1)
    return render_template(
        "cliente/personalizar.html", producto=producto,
        temas=TEMAS_PREDEFINIDOS, materiales_preview=materiales_preview,
    )


# --------------------------------------------------------------- PEDIDOS --

@bp.route("/pedidos")
@login_required
@rol_requerido("CLIENTE")
def mis_pedidos():
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id) \
        .order_by(Pedido.fecha.desc()).all()
    return render_template("cliente/mis_pedidos.html", pedidos=pedidos)


@bp.route("/pedidos/<int:pedido_id>")
@login_required
@rol_requerido("CLIENTE")
def detalle_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.usuario_id != current_user.id:
        return redirect(url_for("cliente.mis_pedidos"))
    atributos = None
    if pedido.personalizacion:
        atributos = json.loads(pedido.personalizacion.atributos_json or "{}")
    return render_template("cliente/detalle_pedido.html", pedido=pedido, atributos=atributos)


@bp.route("/pedidos/<int:pedido_id>/pagar", methods=["GET", "POST"])
@login_required
@rol_requerido("CLIENTE")
def pagar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.usuario_id != current_user.id:
        return redirect(url_for("cliente.mis_pedidos"))
    return render_template("cliente/pagar.html", pedido=pedido)


@bp.route("/perfil")
@login_required
@rol_requerido("CLIENTE")
def perfil():
    return render_template("cliente/perfil.html")
