import os
import requests
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)
import threading

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
    [InlineKeyboardButton("Importar CSV", callback_data='import_csv')],
    [InlineKeyboardButton("Gerar tabela atualizada", callback_data='generate_table')],
    [InlineKeyboardButton("Ver jogos da rodada", callback_data='view_games')],
]

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

async def view_games(update: Update, context: CallbackContext) -> None:
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
        else:
            await context.bot.send_message(
                chat_id=chat_id_global,
                text=f"O arquivo {nome_arquivo} não foi encontrado.",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id_global, text=f"Erro ao ver os jogos da rodada: {str(e)}")

async def import_csv(update: Update, context: CallbackContext) -> None:
    try:
        # Envia mensagem de espera
        await context.bot.send_message(
            chat_id=chat_id_global, 
            text="Olá! Para me enviar a tabela geral, siga esses passos: \n1) Acesse o aplicativo do Parciais\n2) Entre na Bola Quadrada League\n3) Clique no ícone do troféu, no canto direito superior\n4) Ainda no canto direito superior, clique em compartilhar \n5) Em seguida clique em 'Por texto (CSV)'\n6) Selecione o aplicativo Telegram e, logo depois o Bola Quadrada Bot."
        )

        # Executa o arquivo importar_csv.py em uma thread separada
        def run_importar_csv():
            subprocess.run(['python', 'importar_csv.py'], text=True)

        thread = threading.Thread(target=run_importar_csv)
        thread.start()        
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id_global, text=f"Erro ao importar CSV: {str(e)}")

async def generate_table(update: Update, context: CallbackContext) -> None:
    try:                    
        # Envia mensagem de espera
        await context.bot.send_message(
            chat_id=chat_id_global, 
            text="Aguarde alguns segundos pois a tabela está sendo gerada...\nNão costuma demorar mais do que 15 segundos."
        )

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

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id_global, text=f"Erro ao gerar a tabela: {str(e)}")

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()    

    if query.data == 'generate_table':
        await generate_table(update, context)
    
    elif query.data == 'view_games':
        await view_games(update, context)
    
    elif query.data == 'import_csv':
        await import_csv(update, context)

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('verjogos', view_games))
    app.add_handler(CommandHandler('importcsv', import_csv))
    app.add_handler(CommandHandler('gerartabela', generate_table))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == '__main__':
    main()
