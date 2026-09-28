import json
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import (
    Producto, Insumo, RecetaInsumo, Usuario, Pedido, Venta, Alerta, Produccion,
)
from routes.decorators import rol_requerido
from services.inventario import (
    calcular_materiales_requeridos, materiales_suficientes, descontar_insumos,
    verificar_alerta_stock,
)

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@login_required
@rol_requerido("DUENO")
def _restringir_a_dueno():
    pass


@bp.route("/panel")
def dashboard():
    hoy = date.today()
    ventas_hoy = Venta.query.filter(db.func.date(Venta.fecha) == hoy).all()
    total_ventas_hoy = sum(v.total for v in ventas_hoy)

    return render_template(
        "admin/dashboard.html",
        total_ventas_hoy=total_ventas_hoy,
        pedidos_pendientes=Pedido.query.filter_by(estado="PENDIENTE").count(),
        pedidos_produccion=Pedido.query.filter_by(estado="EN_PRODUCCION").count(),
        productos_stock_bajo=Producto.query.filter(Producto.stock <= 3,
                                                     Producto.tipo == "PRODUCTO_LISTO").count(),
        insumos_stock_bajo=[i for i in Insumo.query.all() if i.stock_bajo()],
    )


# ------------------------------------------------------------- PRODUCTOS --

@bp.route("/productos")
def productos():
    return render_template("admin/productos.html", productos=Producto.query.all())


@bp.route("/productos/nuevo", methods=["GET", "POST"])
def producto_nuevo():
    if request.method == "POST":
        p = Producto(
            nombre=request.form["nombre"], descripcion=request.form.get("descripcion", ""),
            categoria=request.form.get("categoria", ""), precio=float(request.form["precio"]),
            tipo=request.form["tipo"], stock=int(request.form.get("stock", 0) or 0),
            horas_estimadas=float(request.form.get("horas_estimadas", 0) or 0),
        )
        db.session.add(p)
        db.session.commit()
        flash("Producto creado.", "success")
        return redirect(url_for("admin.productos"))
    return render_template("admin/producto_form.html", producto=None)


@bp.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
def producto_editar(producto_id):
    p = Producto.query.get_or_404(producto_id)
    if request.method == "POST":
        p.nombre = request.form["nombre"]
        p.descripcion = request.form.get("descripcion", "")
        p.categoria = request.form.get("categoria", "")
        p.precio = float(request.form["precio"])
        p.tipo = request.form["tipo"]
        p.stock = int(request.form.get("stock", 0) or 0)
        p.horas_estimadas = float(request.form.get("horas_estimadas", 0) or 0)
        db.session.commit()
        flash("Producto actualizado.", "success")
        return redirect(url_for("admin.productos"))
    return render_template("admin/producto_form.html", producto=p)


@bp.route("/productos/<int:producto_id>/estado", methods=["POST"])
def producto_toggle_estado(producto_id):
    p = Producto.query.get_or_404(producto_id)
    p.estado = "INACTIVO" if p.estado == "ACTIVO" else "ACTIVO"
    db.session.commit()
    return redirect(url_for("admin.productos"))


# ------------------------------------------------------------------ RECETAS --

@bp.route("/productos/<int:producto_id>/receta", methods=["GET", "POST"])
def receta(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if request.method == "POST":
        insumo_id = int(request.form["insumo_id"])
        cantidad = float(request.form["cantidad_por_unidad"])
        existente = RecetaInsumo.query.filter_by(producto_id=producto.id,
                                                   insumo_id=insumo_id).first()
        if existente:
            existente.cantidad_por_unidad = cantidad
        else:
            db.session.add(RecetaInsumo(producto_id=producto.id, insumo_id=insumo_id,
                                         cantidad_por_unidad=cantidad))
        db.session.commit()
        flash("Receta actualizada.", "success")
        return redirect(url_for("admin.receta", producto_id=producto.id))

    return render_template("admin/receta.html", producto=producto,
                            insumos=Insumo.query.filter_by(estado="ACTIVO").all())


@bp.route("/productos/<int:producto_id>/receta/<int:item_id>/eliminar", methods=["POST"])
def receta_eliminar_item(producto_id, item_id):
    item = RecetaInsumo.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("admin.receta", producto_id=producto_id))


# ------------------------------------------------------------------ INSUMOS --

@bp.route("/insumos")
def insumos():
    return render_template("admin/insumos.html", insumos=Insumo.query.all())


@bp.route("/insumos/nuevo", methods=["GET", "POST"])
def insumo_nuevo():
    if request.method == "POST":
        i = Insumo(
            nombre=request.form["nombre"], unidad=request.form["unidad"],
            stock_actual=float(request.form.get("stock_actual", 0) or 0),
            stock_minimo=float(request.form.get("stock_minimo", 0) or 0),
        )
        db.session.add(i)
        db.session.commit()
        verificar_alerta_stock(i)
        db.session.commit()
        flash("Insumo creado.", "success")
        return redirect(url_for("admin.insumos"))
    return render_template("admin/insumo_form.html", insumo=None)


@bp.route("/insumos/<int:insumo_id>/editar", methods=["GET", "POST"])
def insumo_editar(insumo_id):
    i = Insumo.query.get_or_404(insumo_id)
    if request.method == "POST":
        i.nombre = request.form["nombre"]
        i.unidad = request.form["unidad"]
        i.stock_actual = float(request.form.get("stock_actual", 0) or 0)
        i.stock_minimo = float(request.form.get("stock_minimo", 0) or 0)
        db.session.commit()
        verificar_alerta_stock(i)
        db.session.commit()
        flash("Insumo actualizado.", "success")
        return redirect(url_for("admin.insumos"))
    return render_template("admin/insumo_form.html", insumo=i)


# ------------------------------------------------------------------ PEDIDOS --

@bp.route("/pedidos")
def pedidos():
    filtro = request.args.get("estado", "")
    query = Pedido.query
    if filtro:
        query = query.filter_by(estado=filtro)
    pedidos_lista = query.order_by(Pedido.fecha.desc()).all()
    return render_template("admin/pedidos.html", pedidos=pedidos_lista, filtro=filtro)


@bp.route("/pedidos/<int:pedido_id>")
def pedido_detalle(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    materiales = None
    atributos = None
    if pedido.personalizacion:
        atributos = json.loads(pedido.personalizacion.atributos_json or "{}")
        materiales = calcular_materiales_requeridos(
            pedido.personalizacion.producto, pedido.personalizacion.cantidad
        )
    return render_template("admin/pedido_detalle.html", pedido=pedido,
                            materiales=materiales, atributos=atributos)


@bp.route("/pedidos/<int:pedido_id>/aceptar", methods=["POST"])
def pedido_aceptar(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if not pedido.puede_transicionar_a("ACEPTADO"):
        flash("No se puede aceptar un pedido en este estado.", "danger")
        return redirect(url_for("admin.pedido_detalle", pedido_id=pedido_id))

    # Si es personalizado, descontar insumos de la receta al aceptar
    if pedido.personalizacion:
        prod = pedido.personalizacion.producto
        cant = pedido.personalizacion.cantidad
        descontar_insumos(prod, cant)

    pedido.estado = "ACEPTADO"
    db.session.commit()
    flash("Pedido aceptado.", "success")
    return redirect(url_for("admin.pedido_detalle", pedido_id=pedido_id))


@bp.route("/pedidos/<int:pedido_id>/rechazar", methods=["POST"])
def pedido_rechazar(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if not pedido.puede_transicionar_a("RECHAZADO"):
        flash("No se puede rechazar un pedido en este estado.", "danger")
        return redirect(url_for("admin.pedido_detalle", pedido_id=pedido_id))
    pedido.estado = "RECHAZADO"
    pedido.motivo_rechazo = request.form.get("motivo", "No especificado")
    db.session.commit()
    flash("Pedido rechazado.", "info")
    return redirect(url_for("admin.pedido_detalle", pedido_id=pedido_id))


@bp.route("/pedidos/<int:pedido_id>/entregar", methods=["POST"])
def pedido_entregar(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if not pedido.puede_transicionar_a("ENTREGADO"):
        flash("No se puede marcar como entregado en este estado.", "danger")
        return redirect(url_for("admin.pedido_detalle", pedido_id=pedido_id))
    pedido.estado = "ENTREGADO"
    db.session.commit()
    flash("Pedido marcado como entregado. Inventario actualizado.", "success")
    return redirect(url_for("admin.pedido_detalle", pedido_id=pedido_id))


@bp.route("/pedidos/<int:pedido_id>/asignar", methods=["POST"])
def pedido_asignar(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    empleado_id = int(request.form["empleado_id"])
    empleado = Usuario.query.get_or_404(empleado_id)

    horas_estimadas = 0
    if pedido.personalizacion:
        horas_estimadas = (pedido.personalizacion.producto.horas_estimadas or 0) \
            * pedido.personalizacion.cantidad
    else:
        horas_estimadas = sum((d.producto.horas_estimadas or 0) * d.cantidad
                               for d in pedido.detalles)

    horas_asignadas = db.session.query(db.func.coalesce(db.func.sum(Produccion.horas_estimadas), 0)) \
        .filter(Produccion.empleado_id == empleado.id,
                Produccion.estado != "TERMINADO").scalar()
    horas_restantes = (empleado.horas_disponibles or 0) - horas_asignadas

    if horas_estimadas > horas_restantes:
        flash(f"⚠ Capacidad insuficiente para asignar esta producción a "
              f"{empleado.nombre_completo} (restan {horas_restantes:.1f}h, "
              f"se requieren {horas_estimadas:.1f}h). Puedes continuar de todas formas.",
              "warning")

    fecha_limite_str = request.form.get("fecha_limite")
    fecha_limite = datetime.strptime(fecha_limite_str, "%Y-%m-%d").date() if fecha_limite_str else None

    produccion = Produccion(
        pedido_id=pedido.id, empleado_id=empleado.id, fecha_limite=fecha_limite,
        horas_estimadas=horas_estimadas, estado="PENDIENTE",
    )
    db.session.add(produccion)
    pedido.estado = "EN_PRODUCCION"
    db.session.commit()
    flash("Producción asignada.", "success")
    return redirect(url_for("admin.pedido_detalle", pedido_id=pedido_id))


# ----------------------------------------------------------------- EMPLEADOS --

@bp.route("/empleados")
def empleados():
    return render_template("admin/empleados.html",
                            empleados=Usuario.query.filter_by(rol="EMPLEADO").all())


@bp.route("/empleados/nuevo", methods=["GET", "POST"])
def empleado_nuevo():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        if Usuario.query.filter_by(correo=correo).first():
            flash("Ese correo ya está registrado.", "danger")
            return render_template("admin/empleado_form.html", empleado=None)

        e = Usuario(
            nombre_completo=request.form["nombre_completo"], correo=correo,
            telefono=request.form.get("telefono", ""), rol="EMPLEADO", estado="ACTIVO",
            horas_disponibles=float(request.form.get("horas_disponibles", 40) or 40),
        )
        e.set_password(request.form.get("password") or "miraliz123")
        db.session.add(e)
        db.session.commit()
        flash("Empleado creado. Contraseña temporal: la definida en el formulario "
              "(o 'miraliz123' por defecto).", "success")
        return redirect(url_for("admin.empleados"))
    return render_template("admin/empleado_form.html", empleado=None)


@bp.route("/empleados/<int:usuario_id>/estado", methods=["POST"])
def empleado_toggle_estado(usuario_id):
    e = Usuario.query.get_or_404(usuario_id)
    e.estado = "INACTIVO" if e.estado == "ACTIVO" else "ACTIVO"
    db.session.commit()
    flash(f"Empleado {'desactivado' if e.estado == 'INACTIVO' else 'activado'}.", "info")
    return redirect(url_for("admin.empleados"))


@bp.route("/empleados/<int:usuario_id>/resetear-password", methods=["POST"])
def empleado_resetear_password(usuario_id):
    e = Usuario.query.get_or_404(usuario_id)
    e.set_password("miraliz123")
    db.session.commit()
    flash(f"Contraseña de {e.nombre_completo} restablecida a 'miraliz123'.", "success")
    return redirect(url_for("admin.empleados"))


# -------------------------------------------------------------------- ALERTAS --

@bp.route("/alertas")
def alertas():
    return render_template("admin/alertas.html",
                            alertas=Alerta.query.filter_by(atendida=False)
                            .order_by(Alerta.fecha.desc()).all())


# ------------------------------------------------------------------- REPORTES --

@bp.route("/reportes")
def reportes():
    ventas = Venta.query.all()
    pedidos_todos = Pedido.query.all()
    return render_template(
        "admin/reportes.html",
        total_vendido=sum(v.total for v in ventas),
        num_ventas=len(ventas),
        pedidos_pendientes=len([p for p in pedidos_todos if p.estado == "PENDIENTE"]),
        pedidos_terminados=len([p for p in pedidos_todos if p.estado in ("TERMINADO", "ENTREGADO")]),
        pedidos_rechazados=len([p for p in pedidos_todos if p.estado == "RECHAZADO"]),
        productos_activos=Producto.query.filter_by(estado="ACTIVO").count(),
        insumos_stock_bajo=len([i for i in Insumo.query.all() if i.stock_bajo()]),
    )
