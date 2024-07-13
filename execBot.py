import os
import shutil
import requests
import pandas as pd
from jinja2 import Template
from selenium import webdriver
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    Updater,    
    CallbackContext,
    MessageHandler,
    filters
)
import subprocess  # Importação da biblioteca subprocess

# Token do seu bot do Telegram
TOKEN = '7394461511:AAH09LQq6avJOxlEPtWkRlPkG3e1I2rz2uM'

# Função para obter o número da rodada atual do Cartola FC
def obter_rodada_atual():
    url = "https://api.cartola.globo.com/mercado/status"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rodada_atual = data.get("rodada_atual")
        if rodada_atual is not None:
            return rodada_atual
        else:
            raise ValueError("Campo 'rodada_atual' não encontrado na resposta da API.")
    except Exception as e:
        raise ValueError(f"Erro ao obter número da rodada atual: {str(e)}")

# Obter o número da rodada atual
numero_rodada_atual = obter_rodada_atual()

nome_pasta = f"Rodada {numero_rodada_atual}"
pasta_rodadas = 'Rodadas'

# Criar a pasta "Rodadas" se não existir
if not os.path.exists(pasta_rodadas):
    os.makedirs(pasta_rodadas)

# Criar a pasta da rodada atual dentro da pasta "Rodadas" se não existir
caminho_completo_pasta = os.path.join(pasta_rodadas, nome_pasta)

# Variável global para armazenar o ID do chat
chat_id_global = None

# Opções para o menu principal
MAIN_MENU_KEYBOARD = [
    [InlineKeyboardButton("Gerar tabela atualizada", callback_data='generate_table')],
    [InlineKeyboardButton("Ver jogos da rodada", callback_data='view_games')],
]

# Função para o comando /start
async def start(update: Update, context: CallbackContext) -> None:
    pass  # Não enviamos nenhuma mensagem aqui, apenas a lógica desejada

# Função para obter o número da rodada atual do Cartola FC
def obter_rodada_atual():
    url = "https://api.cartola.globo.com/mercado/status"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rodada_atual = data.get("rodada_atual")
            if rodada_atual is not None:
                return rodada_atual
            else:
                raise ValueError("Campo 'rodada_atual' não encontrado na resposta da API.")
        else:
            raise ValueError(f"Erro ao obter resposta da API: {response.status_code}")
    except Exception as e:
        raise ValueError(f"Erro ao obter número da rodada atual: {str(e)}")

async def start(update: Update, context: CallbackContext) -> None:
    global chat_id_global
    chat_id_global = update.message.chat_id
    
    # Mensagem de boas-vindas
    welcome_message = "Olá! Eu sou o bot da Bola Quadrada! Como posso te ajudar?"
    
    # Envio da mensagem de boas-vindas
    await context.bot.send_message(chat_id=chat_id_global, text=welcome_message)

    # Teclado de opções
    reply_markup = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)
    await update.message.reply_text('Escolha uma opção:', reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'generate_table':       
        try:                    
             # Envia mensagem de espera
            await context.bot.send_message(
                    chat_id=chat_id_global, 
                    text="Aguarde alguns segundos pois a tabela está sendo gerada...\nNão costuma demorar mais do que 15 segundos.")

            # Executa o arquivo atualizar_classificacao.py
            subprocess.run(['python', 'atualizar_classificacao.py'], check=True)
            
            # Carrega a imagem gerada
            image_path = os.path.join(caminho_completo_pasta, f'classificacao_atualizada_rodada{numero_rodada_atual}.png')
            
            # Envia a imagem gerada para o chat onde começou a interação
            await context.bot.send_photo(chat_id=chat_id_global, photo=open(image_path, 'rb'))            

            # Envie a mensagem de conclusão
            await context.bot.send_message(
                    chat_id=chat_id_global,
                    text="Pronto.\nAjudo com algo mais?\nPara visualizar as opções é só clicar abaixo:\n/start",
                    parse_mode='Markdown'
                )

        except Exception    as e:
            await query.edit_message_text(text=f"Erro ao gerar a tabela: {str(e)}")
    
    elif query.data == 'view_games':
        try:
            # Executa o arquivo jogos_da_rodada.py
            subprocess.run(['python', 'jogos_da_rodada.py'], check=True)
            
            # Nome do arquivo de saída
            nome_arquivo = f'jogos_da_rodada_{numero_rodada_atual}.txt'

            # Constrói o caminho completo para o arquivo de jogos
            caminho_arquivo_jogos = os.path.join(caminho_completo_pasta, nome_arquivo)
        
            # Verifica se o arquivo existe antes de tentar abri-lo
            if os.path.exists(caminho_arquivo_jogos):
            
            # Leitura do arquivo de jogos gerado
                with open(caminho_arquivo_jogos, 'r', encoding='utf-8') as file:
                    jogos_text = file.read()

            # Envia os jogos da rodada para o chat onde começou a interação
            await context.bot.send_message(chat_id=chat_id_global, text=jogos_text)
            
            # Envie a mensagem de conclusão
            await context.bot.send_message(
                    chat_id=chat_id_global,
                    text="Pronto.\nAjudo com algo mais?\nPara visualizar as opções é só clicar abaixo:\n/start",
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            await query.edit_message_text(text=f"Erro ao ver os jogos da rodada: {str(e)}")

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == '__main__':
    main()
