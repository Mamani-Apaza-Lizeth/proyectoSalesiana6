# Cotillón MiraLiz - Sistema Web

Proyecto académico (Web III) desarrollado con **Python + Flask + SQLite**,
frontend con **Bootstrap 5**, siguiendo la especificación maestra del sistema.

## Alcance implementado (Prioridad 1 completa + partes de Prioridad 2)

- Registro/login/roles (CLIENTE, EMPLEADO, DUEÑO), control de acceso en backend.
- Catálogo público, productos listos y personalizados.
- Carrito, pedidos, validación de stock en backend (nunca solo en frontend).
- Personalización con formulario dinámico (ej. Mochila, Piñata 2D), opción "Otro".
- Cálculo automático de materiales por receta y validación de stock de insumos.
- Flujo de revisión de pedidos personalizados por el dueño (aceptar/rechazar con motivo).
- Inventario de productos e insumos, alertas de stock bajo + correo (modo desarrollo).
- Producción: asignación a empleados con validación de capacidad (horas).
- Ventas presenciales por empleados, con descuento automático de stock.
- API de pagos simulada (`POST /api/pago`) para EFECTIVO/QR/TARJETA.
- Paneles de cliente, empleado y dueño (incluye reportes básicos).

## Instalación

```bash
cd miraliz
python -m venv venv
source venv/bin/activate       # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py                 # Crea y puebla la base de datos con datos de ejemplo
python app.py                  # Corre en http://127.0.0.1:5000
```

## Usuarios de prueba (creados por seed.py)

| Rol      | Correo                  | Contraseña   |
|----------|--------------------------|--------------|
| Dueño    | dueno@miraliz.com        | admin123     |
| Empleado | empleado@miraliz.com     | empleado123  |
| Cliente  | cliente@miraliz.com      | cliente123   |

## Migración futura a MySQL

Solo se necesita cambiar `SQLALCHEMY_DATABASE_URI` en `config.py` (o la variable
de entorno `DATABASE_URL`) por una cadena de conexión MySQL, por ejemplo:

```
mysql+pymysql://usuario:password@localhost/miraliz
```

Todo el acceso a datos usa SQLAlchemy ORM, por lo que el resto del código
no necesita modificarse.

## Correo (SMTP)

Si no configuras `MAIL_USERNAME` / `MAIL_PASSWORD` como variables de entorno,
el sistema funciona en "modo desarrollo": los correos se imprimen en la
consola en vez de enviarse, para no bloquear las pruebas (sección 7 y 25
de la especificación).

## Estructura del proyecto

```
miraliz/
├── app.py, config.py, extensions.py, seed.py
├── models/       (usuario, inventario, pedido)
├── routes/       (public, auth, cliente, empleado, admin, api)
├── services/     (correo, inventario, pagos)
├── templates/    (base + public + cliente/ + empleado/ + admin/)
└── static/       (css/js/img)
```

## Próximos pasos sugeridos (Prioridad 2/3 restante)

- Pedidos mixtos (listos + personalizados en un mismo carrito).
- Editor visual del wireframe / mejoras de diseño responsive más finas.
- Reportes gráficos (charts) y estadísticas más detalladas.
- Verificación de correo por código al registrarse.
- Migración real a MySQL para producción.
