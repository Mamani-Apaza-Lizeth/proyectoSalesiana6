from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import Producto, Venta, DetalleVenta, Produccion
from routes.decorators import rol_requerido
from services.inventario import validar_stock_producto_listo, verificar_alerta_stock

bp = Blueprint("empleado", __name__, url_prefix="/empleado")


@bp.before_request
@login_required
@rol_requerido("EMPLEADO")
def _restringir_a_empleado():
    pass


@bp.route("/panel")
def dashboard():
    tareas_pendientes = Produccion.query.filter_by(
        empleado_id=current_user.id
    ).filter(Produccion.estado != "TERMINADO").count()
    return render_template("empleado/panel.html", tareas_pendientes=tareas_pendientes)


@bp.route("/venta/nueva", methods=["GET", "POST"])
def nueva_venta():
    productos = Producto.query.filter_by(estado="ACTIVO", tipo="PRODUCTO_LISTO").all()

    if request.method == "POST":
        producto_ids = request.form.getlist("producto_id")
        cantidades = request.form.getlist("cantidad")
        cliente_nombre = request.form.get("cliente_nombre", "Cliente mostrador")
        metodo_pago = request.form.get("metodo_pago", "EFECTIVO")

        venta = Venta(empleado_id=current_user.id, cliente_nombre=cliente_nombre,
                       metodo_pago=metodo_pago, total=0)
        total = 0
        errores = []

        for pid, cant in zip(producto_ids, cantidades):
            if not pid or not cant:
                continue
            producto = Producto.query.get(int(pid))
            cantidad = int(cant)
            if not producto or not validar_stock_producto_listo(producto, cantidad):
                errores.append(f"Stock insuficiente para '{producto.nombre if producto else pid}'.")
                continue
            venta.detalles.append(DetalleVenta(
                producto_id=producto.id, cantidad=cantidad, precio_unitario=producto.precio,
            ))
            producto.stock -= cantidad
            total += producto.precio * cantidad

        if errores or not venta.detalles:
            for e in errores or ["Debes agregar al menos un producto con stock disponible."]:
                flash(e, "danger")
            return render_template("empleado/nueva_venta.html", productos=productos)

        venta.total = total
        db.session.add(venta)
        db.session.commit()
        flash(f"Venta registrada por Bs. {total:.2f}.", "success")
        return redirect(url_for("empleado.historial_ventas"))

    return render_template("empleado/nueva_venta.html", productos=productos)


@bp.route("/ventas")
def historial_ventas():
    ventas = Venta.query.filter_by(empleado_id=current_user.id) \
        .order_by(Venta.fecha.desc()).all()
    return render_template("empleado/historial.html", ventas=ventas)


@bp.route("/tareas")
def mis_tareas():
    tareas = Produccion.query.filter_by(empleado_id=current_user.id) \
        .order_by(Produccion.fecha_asignacion.desc()).all()
    return render_template("empleado/mis_tareas.html", tareas=tareas)


@bp.route("/tareas/<int:tarea_id>/estado", methods=["POST"])
def actualizar_tarea(tarea_id):
    tarea = Produccion.query.get_or_404(tarea_id)
    if tarea.empleado_id != current_user.id:
        flash("No puedes modificar tareas que no tienes asignadas.", "danger")
        return redirect(url_for("empleado.mis_tareas"))

    nuevo_estado = request.form.get("estado")
    if nuevo_estado not in ("PENDIENTE", "EN_PROCESO", "TERMINADO"):
        flash("Estado no válido.", "danger")
        return redirect(url_for("empleado.mis_tareas"))

    tarea.estado = nuevo_estado
    if nuevo_estado == "TERMINADO":
        tarea.pedido.estado = "TERMINADO"
    db.session.commit()
    flash("Tarea actualizada.", "success")
    return redirect(url_for("empleado.mis_tareas"))


@bp.route("/inventario")
def inventario():
    productos = Producto.query.filter_by(estado="ACTIVO").all()
    return render_template("empleado/inventario.html", productos=productos)
