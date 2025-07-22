import click
from flask.cli import with_appcontext
from app import db
from services.scheduler import check_and_process_feeds

def register_commands(app):
    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        """Cria as tabelas do banco de dados."""
        import models  # Importa os modelos para garantir que sejam registrados
        db.create_all()
        click.echo("Banco de dados inicializado.")

    @app.cli.command("run-task")
    @with_appcontext
    def run_task_command():
        """Executa a tarefa de verificação de feeds manualmente."""
        click.echo("Iniciando a tarefa de verificação de feeds...")
        try:
            check_and_process_feeds()
            click.echo("Tarefa concluída com sucesso.")
        except Exception as e:
            click.echo(f"Erro ao executar a tarefa: {e}")