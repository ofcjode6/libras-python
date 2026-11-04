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

    
def criar_tabela_resultados():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultado_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            letra_pergunta TEXT NOT NULL,
            resposta_escolhida TEXT NOT NULL,
            resposta_correta INTEGER NOT NULL,
            data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        )
    """)

    conexao.commit()
    conexao.close()


def criar_tabela_tentativas():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tentativa_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pontuacao INTEGER NOT NULL,
            total_perguntas INTEGER NOT NULL,
            data_tentativa TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        )
    """)

    conexao.commit()
    conexao.close()


def obter_dados_administrativos():
    conexao = conectar()
    cursor = conexao.cursor()

    # Total de alunos cadastrados
    cursor.execute("""
        SELECT COUNT(*)
        FROM usuario
        WHERE tipo = 'aluno'
    """)
    total_alunos = cursor.fetchone()[0]

    # Total de alunos que já realizaram algum quiz
    cursor.execute("""
        SELECT COUNT(DISTINCT usuario_id)
        FROM tentativa_quiz
    """)
    alunos_participantes = cursor.fetchone()[0]

    # Total de tentativas realizadas
    cursor.execute("""
        SELECT COUNT(*)
        FROM tentativa_quiz
    """)
    total_tentativas = cursor.fetchone()[0]

    # Média geral de aproveitamento
    cursor.execute("""
        SELECT
            AVG(
                CAST(pontuacao AS REAL) /
                NULLIF(total_perguntas, 0) * 100
            )
        FROM tentativa_quiz
    """)
    media_aproveitamento = cursor.fetchone()[0] or 0

    # Desempenho individual dos alunos
    cursor.execute("""
        SELECT
            u.nome_usuario,
            MAX(t.pontuacao),
            MAX(t.total_perguntas),
            COUNT(t.id)
        FROM usuario u
        INNER JOIN tentativa_quiz t
            ON u.id = t.usuario_id
        WHERE u.tipo = 'aluno'
        GROUP BY u.id, u.nome_usuario
        ORDER BY MAX(t.pontuacao) DESC
    """)
    desempenho_alunos = cursor.fetchall()

        # Distribuição das pontuações por faixa de aproveitamento
    cursor.execute("""
        SELECT
            CASE
                WHEN (t.pontuacao * 100.0 / t.total_perguntas) <= 20
                    THEN '0-20%'
                WHEN (t.pontuacao * 100.0 / t.total_perguntas) <= 40
                    THEN '21-40%'
                WHEN (t.pontuacao * 100.0 / t.total_perguntas) <= 60
                    THEN '41-60%'
                WHEN (t.pontuacao * 100.0 / t.total_perguntas) <= 80
                    THEN '61-80%'
                ELSE '81-100%'
            END AS faixa,
            COUNT(*) AS quantidade
        FROM tentativa_quiz t
        INNER JOIN usuario u ON u.id = t.usuario_id
        WHERE u.tipo = 'aluno'
          AND t.total_perguntas > 0
        GROUP BY faixa
    """)

    distribuicao_pontuacoes = cursor.fetchall()


        # Evolução do desempenho médio dos alunos por tentativa
    cursor.execute("""
        WITH tentativas_ordenadas AS (
            SELECT
                t.usuario_id,
                (t.pontuacao * 100.0 / t.total_perguntas) AS aproveitamento,
                ROW_NUMBER() OVER (
                    PARTITION BY t.usuario_id
                    ORDER BY t.data_tentativa, t.id
                ) AS numero_tentativa
            FROM tentativa_quiz t
            INNER JOIN usuario u ON u.id = t.usuario_id
            WHERE u.tipo = 'aluno'
              AND t.total_perguntas > 0
        )
        SELECT
            numero_tentativa,
            ROUND(AVG(aproveitamento), 1),
            COUNT(*)
        FROM tentativas_ordenadas
        GROUP BY numero_tentativa
        ORDER BY numero_tentativa
    """)

    evolucao_desempenho = cursor.fetchall()

        # Questões com maior quantidade de erros
    cursor.execute("""
        SELECT
            r.letra_pergunta,
            COUNT(*) AS total_respostas,
            SUM(
                CASE
                    WHEN r.resposta_correta = 0 THEN 1
                    ELSE 0
                END
            ) AS total_erros,
            ROUND(
                SUM(
                    CASE
                        WHEN r.resposta_correta = 0 THEN 1
                        ELSE 0
                    END
                ) * 100.0 / COUNT(*),
                1
            ) AS percentual_erros
        FROM resultado_quiz r
        INNER JOIN usuario u ON u.id = r.usuario_id
        WHERE u.tipo = 'aluno'
        GROUP BY r.letra_pergunta
        ORDER BY total_erros DESC
    """)

    questoes_com_mais_erros = cursor.fetchall()


    conexao.close()

    return {
        "total_alunos": total_alunos,
        "alunos_participantes": alunos_participantes,
        "total_tentativas": total_tentativas,
        "media_aproveitamento": media_aproveitamento,
        "desempenho_alunos": desempenho_alunos,
                "distribuicao_pontuacoes": distribuicao_pontuacoes,
                "evolucao_desempenho": evolucao_desempenho,
                "questoes_com_mais_erros": questoes_com_mais_erros
    } 
 

if __name__ == "__main__":
    criar_tabela_usuario()
    criar_tabela_resultados()
    print("Banco de dados criado com sucesso!")