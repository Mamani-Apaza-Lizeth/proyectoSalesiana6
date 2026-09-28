"""
Poblado inicial de la base de datos con datos de ejemplo, para poder
demostrar el escenario completo descrito en la sección 40 de la
especificación (registro -> catálogo -> pedido -> producción -> entrega).

Ejecutar con:  python seed.py
"""
from app import create_app
from extensions import db
from models import Usuario, Producto, Insumo, RecetaInsumo


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # --- Usuarios ---
        dueno = Usuario(nombre_completo="Liz Rodríguez", correo="dueno@miraliz.com",
                         telefono="70000000", rol="DUENO", estado="ACTIVO")
        dueno.set_password("admin123")

        empleado = Usuario(nombre_completo="Carlos Mamani", correo="empleado@miraliz.com",
                            telefono="70000001", rol="EMPLEADO", estado="ACTIVO",
                            horas_disponibles=40)
        empleado.set_password("empleado123")

        cliente = Usuario(nombre_completo="Ana Pérez", correo="cliente@miraliz.com",
                           telefono="70000002", direccion="Zona Central, La Paz",
                           rol="CLIENTE", estado="ACTIVO", correo_verificado=True)
        cliente.set_password("cliente123")

        db.session.add_all([dueno, empleado, cliente])
        db.session.commit()

        # --- Insumos ---
        cuerina = Insumo(nombre="Cuerina", unidad="METRO", stock_actual=20, stock_minimo=5)
        forro = Insumo(nombre="Forro", unidad="METRO", stock_actual=15, stock_minimo=4)
        cierre = Insumo(nombre="Cierre", unidad="UNIDAD", stock_actual=30, stock_minimo=10)
        carton = Insumo(nombre="Cartón", unidad="UNIDAD", stock_actual=10, stock_minimo=5)
        silicona = Insumo(nombre="Silicona", unidad="LITRO", stock_actual=2, stock_minimo=3)  # bajo a propósito
        db.session.add_all([cuerina, forro, cierre, carton, silicona])
        db.session.commit()

        # --- Productos listos ---
        vaso = Producto(nombre="Vasos descartables (paquete x10)", categoria="Vajilla",
                         precio=8, tipo="PRODUCTO_LISTO", stock=50, estado="ACTIVO")
        plato = Producto(nombre="Platos descartables (paquete x10)", categoria="Vajilla",
                          precio=10, tipo="PRODUCTO_LISTO", stock=40, estado="ACTIVO")
        globo = Producto(nombre="Globos metálicos (unidad)", categoria="Decoración",
                          precio=15, tipo="PRODUCTO_LISTO", stock=25, estado="ACTIVO")
        db.session.add_all([vaso, plato, globo])
        db.session.commit()

        # --- Productos personalizados ---
        mochila = Producto(nombre="Mochila", descripcion="Mochila personalizada temática",
                            categoria="Personalizados", precio=50,
                            tipo="PRODUCTO_PERSONALIZADO", horas_estimadas=2, estado="ACTIVO")
        pinata = Producto(nombre="Piñata 2D", descripcion="Piñata personalizada temática",
                           categoria="Personalizados", precio=35,
                           tipo="PRODUCTO_PERSONALIZADO", horas_estimadas=1.5, estado="ACTIVO")
        db.session.add_all([mochila, pinata])
        db.session.commit()

        # --- Recetas ---
        db.session.add_all([
            RecetaInsumo(producto_id=mochila.id, insumo_id=cuerina.id, cantidad_por_unidad=1.5),
            RecetaInsumo(producto_id=mochila.id, insumo_id=forro.id, cantidad_por_unidad=1),
            RecetaInsumo(producto_id=mochila.id, insumo_id=cierre.id, cantidad_por_unidad=1),
            RecetaInsumo(producto_id=pinata.id, insumo_id=carton.id, cantidad_por_unidad=2),
            RecetaInsumo(producto_id=pinata.id, insumo_id=silicona.id, cantidad_por_unidad=0.3),
        ])
        db.session.commit()

        print("Base de datos poblada correctamente.")
        print("Usuarios de prueba:")
        print("  Dueño:    dueno@miraliz.com    / admin123")
        print("  Empleado: empleado@miraliz.com / empleado123")
        print("  Cliente:  cliente@miraliz.com  / cliente123")


if __name__ == "__main__":
    run()
