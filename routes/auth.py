from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import Usuario
from services.correo import enviar_bienvenida

bp = Blueprint("auth", __name__)


def _redirigir_segun_rol(usuario):
    if usuario.rol == "DUENO":
        return redirect(url_for("admin.dashboard"))
    if usuario.rol == "EMPLEADO":
        return redirect(url_for("empleado.dashboard"))
    return redirect(url_for("cliente.dashboard"))


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return _redirigir_segun_rol(current_user)

    if request.method == "POST":
        nombre = request.form.get("nombre_completo", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        password = request.form.get("password", "")
        confirmacion = request.form.get("confirmacion", "")

        errores = []
        if not nombre or not correo or not password:
            errores.append("Todos los campos obligatorios deben completarse.")
        if password != confirmacion:
            errores.append("Las contraseñas no coinciden.")
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        if Usuario.query.filter_by(correo=correo).first():
            errores.append("Ese correo ya está registrado.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("registro.html", form=request.form)

        usuario = Usuario(
            nombre_completo=nombre, correo=correo, telefono=telefono,
            direccion=direccion, rol="CLIENTE", estado="ACTIVO",
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()

        enviar_bienvenida(usuario)

        flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("registro.html", form={})


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirigir_segun_rol(current_user)

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario is None or not usuario.check_password(password):
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template("login.html")

        if usuario.estado != "ACTIVO":
            flash("Esta cuenta está desactivada. Contacta al administrador.", "danger")
            return render_template("login.html")

        login_user(usuario)
        return _redirigir_segun_rol(usuario)

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("public.index"))
