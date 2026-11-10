# SIAI — Demonstração pública (somente leitura)

Esta é uma cópia separada da versão local do SIAI. Não conecta à ESP32 e não permite cadastros ou alterações via interface. Todos os dados são fictícios.

## Render (Web Service)
1. Envie os arquivos desta pasta para um repositório GitHub novo. Não envie arquivos `.db`, `.env`, tokens ou dados reais.
2. No Render, crie **New > Web Service**, conecte o repositório e selecione **Python**.
3. Root directory: deixe vazio se o repositório contiver diretamente `app.py`; use `armario_inteligente_web` se a pasta estiver dentro do repositório.
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`
6. Escolha uma modalidade disponível, configure a região e publique.
7. Abra o endereço `.onrender.com` fornecido pelo Render.

O banco de dados SQLite é criado em `/tmp/siai_demo.db`. Em hospedagens efêmeras, os dados de demonstração podem ser reiniciados após redeploy ou reinício. Não usar para dados reais.

## Limitações e segurança
- Rotas POST bloqueadas e API da ESP32 desativada nesta demonstração.
- Exportação CSV desativada.
- Os dados exibidos são fictícios; não representam leituras biométricas reais.
- Não usar esta versão para controlar fechaduras ou gerenciar informações pessoais reais.
- Para implantação real, é necessária autenticação, autorização, proteção CSRF, configuração segura de banco de dados e revisão de segurança.
