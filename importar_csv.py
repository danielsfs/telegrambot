import os
import requests
import datetime
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext

# Token do seu bot do Telegram
TELEGRAM_TOKEN = '7394461511:AAH09LQq6avJOxlEPtWkRlPkG3e1I2rz2uM'

# Pastas onde os arquivos serão salvos
IMPORT_FOLDER = 'Importações'
CURRENT_ROUND_FOLDER = os.path.join(IMPORT_FOLDER, 'Rodada Atual')
OLD_FOLDER = os.path.join(IMPORT_FOLDER, 'Old')
SEQUENTIAL_FILE = os.path.join(CURRENT_ROUND_FOLDER, 'sequential.txt')

# URLs das APIs públicas do Cartola FC
url_mercado = 'https://api.cartolafc.globo.com/mercado/status'
url_clubes = 'https://api.cartolafc.globo.com/clubes'

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

async def handle_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    rodada_atual = obter_rodada_atual()

    # Criar subdiretórios baseados na data atual
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    save_path = os.path.join(IMPORT_FOLDER, date_str)
    os.makedirs(save_path, exist_ok=True)
    os.makedirs(CURRENT_ROUND_FOLDER, exist_ok=True)
    os.makedirs(OLD_FOLDER, exist_ok=True)

    # Criar o DataFrame a partir do texto
    lines = text.strip().split('\n')
    data = [line.split(',') for line in lines]
    
    try:
        df = pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        await update.message.reply_text(f'Erro ao criar o DataFrame: {e}')
        return

    # Verificar se o DataFrame contém todas as colunas necessárias
    REQUIRED_COLUMNS = [
        'posicao', 'timeId', 'time', 'cartola', 'pontos', 
        'vitorias', 'empates', 'derrotas', 'pontos_cartola'
    ]
    
    if all(column in df.columns for column in REQUIRED_COLUMNS):
        # Ler o número sequencial da rodada
        if os.path.exists(SEQUENTIAL_FILE):
            with open(SEQUENTIAL_FILE, 'r') as f:
                sequential = int(f.read().strip()) + 1
        else:
            sequential = 1

        # Novo nome do arquivo
        new_file_name = f"Rodada_{rodada_atual}_{sequential}.csv"
        new_file_path = os.path.join(CURRENT_ROUND_FOLDER, new_file_name)

        # Mover o arquivo CSV antigo para a pasta 'Old'
        for old_file in os.listdir(CURRENT_ROUND_FOLDER):
            if old_file != 'sequential.txt':
                try:
                    old_file_path = os.path.join(CURRENT_ROUND_FOLDER, old_file)
                    old_file_dest = os.path.join(OLD_FOLDER, old_file)
                    os.rename(old_file_path, old_file_dest)
                except Exception as e:
                    await update.message.reply_text(f'Erro ao mover o arquivo antigo: {e}')
                    return
        
        try:
            # Salvar o DataFrame como CSV
            df.to_csv(new_file_path, index=False)
        except Exception as e:
            await update.message.reply_text(f'Erro ao salvar o arquivo CSV: {e}')
            return

        # Atualizar o número sequencial
        with open(SEQUENTIAL_FILE, 'w') as f:
            f.write(str(sequential))

        await update.message.reply_text(f'Arquivo {new_file_name} salvo em {CURRENT_ROUND_FOLDER}')        
    else:
        await update.message.reply_text(f'O texto não contém as colunas necessárias: {", ".join(REQUIRED_COLUMNS)}')

def main() -> None:
    # Criação do ApplicationBuilder
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Iniciar o bot
    application.run_polling()

if __name__ == '__main__':
    # Certifique-se de que as pastas principais existem
    os.makedirs(IMPORT_FOLDER, exist_ok=True)
    os.makedirs(CURRENT_ROUND_FOLDER, exist_ok=True)
    os.makedirs(OLD_FOLDER, exist_ok=True)
    
    main()
