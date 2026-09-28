from functools import wraps
from flask import abort
from flask_login import current_user


def rol_requerido(*roles_permitidos):
    """Bloquea el acceso a la ruta si el rol del usuario autenticado (obtenido
    desde la sesión, nunca desde el navegador) no está en roles_permitidos."""
    def decorador(f):
        @wraps(f)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.rol not in roles_permitidos:
                abort(403)
            return f(*args, **kwargs)
        return envoltura
    return decorador
