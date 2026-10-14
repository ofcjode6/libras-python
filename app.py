from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.database import criar_tabela_usuario, conectar


app = Flask(__name__)

app.secret_key = "chave-do-projeto-aprendendo-libras"


criar_tabela_usuario()


@app.route("/")
def inicio():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    nome_usuario = request.form["nome_usuario"]
    senha = request.form["senha"]

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT id, nome_usuario, senha_hash, tipo
        FROM usuario
        WHERE nome_usuario = ?
        """,
        (nome_usuario,)
    )

    usuario = cursor.fetchone()

    conexao.close()

   
    if usuario is None:
        return "Usuário ou senha incorretos."

    
    senha_correta = check_password_hash(
        usuario[2],
        senha
    )

    if not senha_correta:
        return "Usuário ou senha incorretos."

    session["usuario_id"] = usuario[0]
    session["nome_usuario"] = usuario[1]
    session["tipo"] = usuario[3]

    return redirect(url_for("home"))



@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/cadastrar", methods=["POST"])
def cadastrar():

    nome_usuario = request.form["nome_usuario"]
    senha = request.form["senha"]

    senha_hash = generate_password_hash(senha)

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO usuario (nome_usuario, senha_hash)
            VALUES (?, ?)
            """,
            (nome_usuario, senha_hash)
        )

        conexao.commit()

    except Exception:

        conexao.close()

        return "Erro: esse nome de usuário já pode estar cadastrado."

    conexao.close()

    return redirect(url_for("inicio"))


@app.route("/home")
def home():


    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template(
        "home.html",
        nome_usuario=session["nome_usuario"]
    )



@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)