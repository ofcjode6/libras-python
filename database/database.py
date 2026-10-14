import sqlite3


def conectar():
    conexao = sqlite3.connect("database.db")
    return conexao


def criar_tabela_usuario():
    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'aluno',
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conexao.commit()
    conexao.close()


if __name__ == "__main__":
    criar_tabela_usuario()
    print("Banco de dados criado com sucesso!")