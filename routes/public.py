from flask import Blueprint, render_template, request
from models import Producto

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    destacados = Producto.query.filter_by(estado="ACTIVO", tipo="PRODUCTO_LISTO").limit(4).all()
    return render_template("index.html", destacados=destacados)


@bp.route("/catalogo")
def catalogo():
    busqueda = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()

    query = Producto.query.filter_by(estado="ACTIVO")
    if busqueda:
        query = query.filter(Producto.nombre.ilike(f"%{busqueda}%"))
    if categoria:
        query = query.filter_by(categoria=categoria)

    productos = query.order_by(Producto.tipo, Producto.nombre).all()
    categorias = [c[0] for c in Producto.query.with_entities(Producto.categoria).distinct() if c[0]]

    return render_template("catalogo.html", productos=productos, categorias=categorias,
                            busqueda=busqueda, categoria_actual=categoria)


@bp.route("/producto/<int:producto_id>")
def detalle_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    return render_template("detalle_producto.html", producto=producto)


@bp.route("/contacto")
def contacto():
    return render_template("contacto.html")
