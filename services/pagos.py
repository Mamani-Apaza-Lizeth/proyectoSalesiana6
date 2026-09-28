"""
API de pagos simulada (sección 19).

No se integra ninguna pasarela bancaria real ni se almacenan números de
tarjeta. Para EFECTIVO se aprueba directamente (pago presencial). Para QR y
TARJETA se simula una respuesta de aprobación con una probabilidad alta de
éxito, generando un transaction_id ficticio.
"""
import random
import string


def procesar_pago(pedido_id, monto, metodo):
    metodo = (metodo or "").upper()
    if metodo not in ("EFECTIVO", "QR", "TARJETA"):
        return {"status": "error", "message": "Método de pago no válido."}

    if metodo == "EFECTIVO":
        aprobado = True
    else:
        # Simulación: 92% de probabilidad de aprobación
        aprobado = random.random() < 0.92

    if aprobado:
        tx_id = "TX-" + "".join(random.choices(string.digits, k=5))
        return {
            "status": "success",
            "transaction_id": tx_id,
            "message": "Pago aprobado",
            "pedido_id": pedido_id,
            "monto": monto,
            "metodo": metodo,
        }
    else:
        return {
            "status": "failed",
            "transaction_id": None,
            "message": "Pago rechazado por la entidad emisora. Intenta nuevamente.",
            "pedido_id": pedido_id,
            "monto": monto,
            "metodo": metodo,
        }
