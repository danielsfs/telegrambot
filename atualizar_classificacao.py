import os
import requests
import pandas as pd
from jinja2 import Template
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

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

try:
    # Obter o número da rodada atual
    numero_rodada_atual = obter_rodada_atual()

    nome_pasta = f"Rodada {numero_rodada_atual}"
    pasta_rodadas = 'Rodadas'

    # Criar a pasta "Rodadas" se não existir
    if not os.path.exists(pasta_rodadas):
        os.makedirs(pasta_rodadas)

    # Criar a pasta da rodada atual dentro da pasta "Rodadas" se não existir
    caminho_completo_pasta = os.path.join(pasta_rodadas, nome_pasta)
    if not os.path.exists(caminho_completo_pasta):
        os.makedirs(caminho_completo_pasta)

    # Carregar os CSVs
    rodada_1turno = pd.read_csv('Primeiro Turno/1turno.csv').sort_values('timeId').reset_index(drop=True)
    
    # Procurar o único arquivo CSV na pasta "Importações/Rodada Atual"
    current_round_folder = 'Importações/Rodada Atual'
    files = os.listdir(current_round_folder)
    csv_files = [file for file in files if file.endswith('.csv')]

    if len(csv_files) == 1:
        csv_file_path = os.path.join(current_round_folder, csv_files[0])
        rodada_atual_df = pd.read_csv(csv_file_path).sort_values('timeId').reset_index(drop=True)
    else:
        raise FileNotFoundError("Não foi encontrado exatamente um arquivo CSV na pasta 'Importações/Rodada Atual'.")

    # Calcular as diferenças a partir da rodada atual
    rodada_atual_df[['pontos', 'vitorias', 'empates', 'derrotas', 'pontos_cartola']] -= rodada_1turno[['pontos', 'vitorias', 'empates', 'derrotas', 'pontos_cartola']]
    rodada_atual_df['pontos_cartola'] = rodada_atual_df['pontos_cartola'].round(2)

    # Selecionar e ordenar as colunas desejadas
    nova_classificacao = rodada_atual_df[['posicao', 'time', 'pontos', 'vitorias', 'empates', 'derrotas', 'pontos_cartola']]
    nova_classificacao = nova_classificacao.sort_values(by=['pontos', 'vitorias', 'pontos_cartola'], ascending=[False, False, False]).reset_index(drop=True)
    nova_classificacao['posicao'] = nova_classificacao.index + 1

    # Renomear as colunas
    nova_classificacao.rename(columns={
        'pontos': 'P',
        'vitorias': 'V',
        'empates': 'E',
        'derrotas': 'D',
        'pontos_cartola': 'PC'
    }, inplace=True)

    # Gerar HTML da tabela
    html_template = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }
            .table-container { margin: 0 auto; overflow-x: auto; }
            table { width: auto; max-width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 16px; text-align: center; }
            th, td { padding: 8px 10px; border: 1px solid #dddddd; text-align: center; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            thead tr { background-color: #009879; color: #ffffff; text-align: center; }
            th { background-color: #009879; color: #ffffff; font-size: 14px; text-align: center; }
            tbody tr { border-bottom: 1px solid #dddddd; text-align: center; }
            tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
            tbody tr:last-of-type { border-bottom: 2px solid #009879; }
            tbody tr.green { background-color: #d4edda !important; }
            tbody tr.red { background-color: #f8d7da !important; }
            tbody tr:hover { background-color: #f1f1f1; }
        </style>
    </head>
    <body>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">Posição</th>
                        <th style="width: 150px;">Time</th>
                        <th style="width: 20px;">P</th>
                        <th style="width: 20px;">V</th>
                        <th style="width: 20px;">E</th>
                        <th style="width: 20px;">D</th>
                        <th style="width: 20px;">PC</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in data %}
                    <tr class="{% if row['posicao'] <= 4 %}green{% elif row['posicao'] >= 17 %}red{% endif %}">
                        <td>{{ row['posicao'] }}</td>
                        <td>{{ row['time'] }}</td>
                        <td>{{ row['P'] }}</td>
                        <td>{{ row['V'] }}</td>
                        <td>{{ row['E'] }}</td>
                        <td>{{ row['D'] }}</td>
                        <td>{{ '%.2f'|format(row['PC']) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    template = Template(html_template)
    html_content = template.render(data=nova_classificacao.to_dict(orient='records'))

    # Salvar o HTML em um arquivo
    caminho_arquivo_html = os.path.join(caminho_completo_pasta, f"classificacao_rodada_{numero_rodada_atual}.html")
    with open(caminho_arquivo_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Configurar o Selenium WebDriver com Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get(f"file://{os.path.abspath(caminho_arquivo_html)}")

    # Esperar até que a tabela esteja presente na página
    driver.implicitly_wait(5)  # Reduzir o tempo de espera implícita para 5 segundos

    # Ajustar a altura da janela do navegador para caber toda a tabela
    tabela = driver.find_element(By.TAG_NAME, "table")
    tabela_height = tabela.size["height"]
    driver.set_window_size(1920, tabela_height + 100)

    # Capturar a tabela
    caminho_imagem = os.path.join(caminho_completo_pasta, f"classificacao_atualizada_rodada{numero_rodada_atual}.png")
    tabela.screenshot(caminho_imagem)

    driver.quit()
    
except ValueError as ve:
    print(f"Erro: {ve}")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {str(e)}")
