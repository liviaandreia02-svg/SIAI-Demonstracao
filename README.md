# Armário Inteligente — versão web local

## Como iniciar (Windows)
1. Extraia o ZIP.
2. Instale Python 3.10+.
3. Execute `iniciar_windows.bat`.
4. Abra http://127.0.0.1:5000 no navegador.

O banco SQLite `armario.db` é criado automaticamente. A aplicação oferece cadastro de usuários (nome, matrícula, ID biométrico), salas, armários, histórico com filtros e exportação CSV. Há um endpoint `POST /api/access` para receber eventos do ESP32. Configure a variável de ambiente `ESP32_API_TOKEN` com um token próprio e envie-o no cabeçalho `X-API-Token`.

JSON esperado no endpoint: `{"biometric_id":"BIO-001","result":"Autorizado","reason":"","cabinet_id":1}`. `result` deve ser `Autorizado` ou `Negado`.

A aplicação armazena somente o ID biométrico, não a imagem ou o modelo da impressão digital. O cadastro físico da digital é feito no sensor. A integração ESP32 não vem pré-configurada: é necessário adaptar o código do controlador e definir o endereço de rede. Não exponha este servidor à internet. Use dados fictícios nos testes e considere a LGPD antes de uso institucional. A hora é a do computador servidor.
