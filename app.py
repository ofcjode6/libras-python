
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from database.database import (
    criar_tabela_usuario,
    criar_tabela_resultados,
    criar_tabela_tentativas,
    conectar,
    parametro_sql
)
from database.database import obter_dados_administrativos
from dados.perguntas import perguntas


app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "chave-temporaria-desenvolvimento")


criar_tabela_usuario()
criar_tabela_resultados()
criar_tabela_tentativas()


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
    f"""
    SELECT id, nome_usuario, senha_hash, tipo
    FROM usuario
    WHERE nome_usuario = {parametro_sql()}
    """,
    (nome_usuario,)
)

    usuario = cursor.fetchone()

    conexao.close()

   
    if usuario is None:
       flash("Usuário ou senha incorretos!", "erro")
       return redirect(url_for("inicio"))

    
    senha_correta = check_password_hash(
        usuario[2],
        senha
    )

    if not senha_correta:
       flash("Usuário ou senha incorretos!", "erro")
       return redirect(url_for("inicio"))

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
        f"""
        INSERT INTO usuario (nome_usuario, senha_hash)
        VALUES ({parametro_sql()}, {parametro_sql()})
        """,
        (nome_usuario, senha_hash)
    )

        conexao.commit()

    except Exception as erro:
        conexao.rollback()

    if "unique" in str(erro).lower() or "duplicate" in str(erro).lower():
        conexao.close()

        return render_template(
            "cadastro.html",
            erro="Esse nome de usuário já está cadastrado!"
        )

    conexao.close()
    raise erro

    return redirect(url_for("inicio"))

@app.route("/home")
def home():


    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template(
        "home.html",
        nome_usuario=session["nome_usuario"]
    )

@app.route("/conteudos")
def conteudos():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("conteudos.html")

@app.route("/alfabeto")
def alfabeto():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("alfabeto.html")

@app.route("/numeros")
def numeros():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("numeros.html")


@app.route("/quiz")
def quiz():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("apresentacao_quiz.html")

@app.route("/iniciar-quiz")
def iniciar_quiz():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template(
        "quiz.html",
        perguntas=perguntas
    )

@app.route("/informacoes") 
def informacoes():
     if "usuario_id" not in session: 
        return redirect(url_for("inicio")) 
        
     return render_template("informacoes.html")


@app.route("/historico")
def historico():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
    f"""
    SELECT id, pontuacao, total_perguntas, data_tentativa
    FROM tentativa_quiz
    WHERE usuario_id = {parametro_sql()}
    ORDER BY data_tentativa DESC, id DESC
    """,
    (session["usuario_id"],)
)

    tentativas = cursor.fetchall()
    conexao.close()

    return render_template(
        "historico.html",
        tentativas=tentativas
    )



@app.route("/ranking")
def ranking():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            u.nome_usuario,
            MAX(t.pontuacao) AS melhor_pontuacao,
            MAX(t.total_perguntas) AS total_perguntas
        FROM usuario u
        INNER JOIN tentativa_quiz t
            ON u.id = t.usuario_id
        GROUP BY u.id, u.nome_usuario
        ORDER BY
            MAX(t.pontuacao) DESC,
            u.nome_usuario ASC
    """)

    participantes = cursor.fetchall()
    conexao.close()

    return render_template(
        "ranking.html",
        participantes=participantes
    )

@app.route("/responder-quiz", methods=["POST"])
def responder_quiz():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    usuario_id = session["usuario_id"]
    pontuacao = 0
    total = len(perguntas)

    conexao = conectar()
    cursor = conexao.cursor()

    for pergunta in perguntas:

        identificador = str(pergunta["id"])

        resposta = request.form.get(
            f"resposta_{identificador}", ""
        ).strip()

        correta = resposta == pergunta["resposta_correta"]

        if correta:
            pontuacao += 1

        cursor.execute(
    f"""
    INSERT INTO resultado_quiz
    (usuario_id, letra_pergunta, resposta_escolhida, resposta_correta)
    VALUES (
        {parametro_sql()},
        {parametro_sql()},
        {parametro_sql()},
        {parametro_sql()}
    )
    """,
    (
        usuario_id,
        identificador,
        resposta,
        1 if correta else 0
    )
)

    # Registrar apenas uma tentativa ao finalizar o quiz
    cursor.execute(
    f"""
    INSERT INTO tentativa_quiz
    (usuario_id, pontuacao, total_perguntas)
    VALUES (
        {parametro_sql()},
        {parametro_sql()},
        {parametro_sql()}
    )
    """,
    (usuario_id, pontuacao, total)
)
    conexao.commit()
    conexao.close()

    return render_template(
        "resultado_quiz.html",
        pontuacao=pontuacao,
        total=total
    )


@app.route("/admin")
def admin():
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session.get("tipo") != "admin":
        return redirect(url_for("home"))

    dados = obter_dados_administrativos()

    return render_template(
        "admin.html",
        dados=dados
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)