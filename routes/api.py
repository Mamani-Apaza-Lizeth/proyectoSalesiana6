from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from extensions import db
from models import Pedido, Pago
from services.pagos import procesar_pago

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/pago", methods=["POST"])
@login_required
def registrar_pago():
    data = request.get_json(silent=True) or {}
    pedido_id = data.get("pedido_id")
    monto = data.get("monto")
    metodo = data.get("metodo")

    pedido = Pedido.query.get(pedido_id)
    if pedido is None or pedido.usuario_id != current_user.id:
        return jsonify({"status": "error", "message": "Pedido no encontrado."}), 404

    resultado = procesar_pago(pedido_id, monto, metodo)

    pago = Pago(
        pedido_id=pedido.id, monto=monto, metodo=(metodo or "").upper(),
        estado="APROBADO" if resultado["status"] == "success" else "RECHAZADO",
        transaction_id=resultado.get("transaction_id"),
    )
    db.session.add(pago)

    if resultado["status"] == "success":
        pedido.anticipo = (pedido.anticipo or 0) + float(monto)

    db.session.commit()
    return jsonify(resultado)
