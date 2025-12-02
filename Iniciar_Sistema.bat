@echo off
TITLE Servidor de Cobranca (NAO FECHE ESTA JANELA)
COLOR 0A

echo ==========================================
echo      INICIANDO SISTEMA DE COBRANCA
echo ==========================================
echo.

:: 1. Entra na pasta do projeto
cd /d "C:\sistema_cobranca"

:: 2. Ativa o Ambiente Virtual e roda o Waitress
:: O comando 'call' garante que o script continue
call venv\Scripts\activate.bat

echo.
echo Servidor rodando em: http://localhost:8000
echo Para acessar de outra maquina, use o IP deste computador.
echo.
echo Pressione CTRL+C para parar o servidor.
echo.

:: 3. Inicia o servidor de producao
waitress-serve --listen=*:8000 config.wsgi:application

pause