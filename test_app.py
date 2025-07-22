import pytest
from app import app as flask_app, db
import os
import tempfile

from unittest import mock
from models import Article
@pytest.fixture
def app():
    """Cria e configura uma nova instância da app para cada teste com um banco de dados temporário."""
    
    # Cria um arquivo de banco de dados temporário para isolar os testes
    db_fd, db_path = tempfile.mkstemp()
    
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,  # Desabilita CSRF em formulários para testes
    })

    with flask_app.app_context():
        # Importa os modelos para garantir que sejam registrados antes de create_all
        import models
        db.create_all()

    yield flask_app # O teste é executado aqui

    # Bloco de limpeza executado após o teste
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Um cliente de teste para a aplicação."""
    return app.test_client()

def test_home_page(client):
    """Testa se a página inicial retorna um status 200 OK."""
    response = client.get('/')
    assert response.status_code == 200
    # Adiciona uma verificação de conteúdo para garantir que a página correta foi renderizada.
    # Supondo que seu dashboard tenha o título "Dashboard".
    assert b'Dashboard' in response.data

def test_run_task_command_with_mocks(app, db):
    """
    Testa o comando 'flask run-task', simulando (mocking) as interações
    com os serviços externos (RSS, AI, WordPress).
    """
    # 1. Setup: Criar um artigo 'pending' no banco de dados de teste
    with app.app_context():
        test_article = Article(
            original_url='http://test.com/article1',
            original_title='Test Title',
            original_content='Some content.',
            feed_type='movies',
            status='pending'
        )
        db.session.add(test_article)
        db.session.commit()
        article_id = test_article.id

    # 2. Mocking: Simular os serviços externos
    # Usamos mock.patch para substituir os métodos reais por simulações.
    # A ordem dos decorators é invertida nos argumentos da função.
    @mock.patch('services.scheduler.WordPressPublisher.publish_processed_articles', return_value=1)
    @mock.patch('services.scheduler.AIProcessor.process_pending_articles')
    @mock.patch('services.scheduler.RSSMonitor.fetch_new_articles', return_value=0)
    def run_test(mock_fetch, mock_process, mock_publish):
        # Configura o mock do AIProcessor para simular o processamento
        def process_side_effect(*args, **kwargs):
            article = db.session.get(Article, article_id)
            article.status = 'processed'
            article.titulo_final = 'Título Processado pelo Mock'
            db.session.commit()
            return 1 # Simula que 1 artigo foi processado
        
        mock_process.side_effect = process_side_effect

        # 3. Execução: Rodar o comando CLI
        runner = app.test_cli_runner()
        result = runner.invoke(args=["run-task"])

        # 4. Asserts: Verificar os resultados
        assert 'Tarefa concluída com sucesso.' in result.output
        mock_fetch.assert_called_once()
        mock_process.assert_called_once()
        mock_publish.assert_called_once()

        # Verifica se o artigo foi realmente atualizado no banco de dados
        processed_article = db.session.get(Article, article_id)
        assert processed_article.status == 'processed'
        assert processed_article.titulo_final == 'Título Processado pelo Mock'

    run_test()