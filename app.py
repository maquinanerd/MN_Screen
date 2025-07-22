import os
import logging
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configuração do log
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Definição da classe Base para mapeamento de modelos
class Base(DeclarativeBase):
    pass

# Inicialização do banco de dados
db = SQLAlchemy(model_class=Base)

# Criação da aplicação Flask
app = Flask(__name__)

# Definindo a chave secreta para a sessão (em produção, altere para um valor seguro)
app.secret_key = os.getenv("SESSION_SECRET", "your-secret-key-change-in-production")

# Aplicando middleware para lidar com proxies reversos (para servidores em produção)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuração do banco de dados (substituindo com as credenciais fornecidas)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@host/db" # Valor padrão para desenvolvimento local
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,  # Tempo para reciclar conexões inativas
    "pool_pre_ping": True,  # Verifica a conexão antes de usar
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Desabilita notificações de modificações de objetos

# Inicializa a extensão do banco de dados com a aplicação Flask
db.init_app(app)

# Importando os blueprints das rotas
from routes.dashboard import dashboard_bp
from routes.api import api_bp

# Registrando os blueprints na aplicação Flask
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp, url_prefix='/api')
 
# Importando e registrando os comandos CLI
from commands import register_commands
register_commands(app)
 
# Inicializando o agendador de tarefas
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    from services.scheduler import init_scheduler
    init_scheduler()
    logger.info("Scheduler initialized.")
 
logger.info("Content Automation System initialized successfully")
