import shutil
import requests
import os

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

# Cabeçalhos da solicitação
headers = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Função para formatar a data e hora
def formatar_data_hora(data_hora):
    data, hora = data_hora.split()
    hora_formatada = hora[:5]  # Pegar apenas hh:mm
    data_formatada = "/".join(reversed(data.split("-")))  # Formato dd/mm/aaaa
    return f"{data_formatada} às {hora_formatada}"

# Obter o mapeamento de IDs para nomes dos clubes
def obter_mapeamento_clubes():
    response = requests.get(url_clubes, headers=headers)
    response.raise_for_status()
    clubes = response.json()
    return {str(clube['id']): clube for clube in clubes.values()}

# Função para obter o nome do time pelo ID
def nome_do_time_por_id(clubes, id_time):
    return clubes.get(str(id_time), {'nome': 'Desconhecido'})['nome']

# Função para verificar se a partida já ocorreu
def partida_ocorreu(placar_casa, placar_visitante):
    return placar_casa is not None and placar_visitante is not None

# Tentativa de obter informações do mercado e da rodada atual
try:
    # Obter o número da rodada atual
    rodada_atual = obter_rodada_atual()

    # Criar o nome da pasta com base na rodada atual
    pasta_rodadas = 'Rodadas'
    nome_pasta = f"Rodada {rodada_atual}"
            
    # Criar a pasta "Rodadas" se não existir
    if not os.path.exists(pasta_rodadas):
        os.makedirs(pasta_rodadas)

    # Criar a pasta da rodada atual dentro da pasta "Rodadas" se não existir
    caminho_completo_pasta = os.path.join(pasta_rodadas, nome_pasta)
    if not os.path.exists(caminho_completo_pasta):
        os.makedirs(caminho_completo_pasta)

    response = requests.get(url_mercado, headers=headers)
    response.raise_for_status()

    mercado_status = response.json()
    rodada_atual = mercado_status.get('rodada_atual', None)

    if rodada_atual is not None:
        # Obter mapeamento de clubes
        clubes = obter_mapeamento_clubes()
        
        # URL da API pública do Cartola FC para obter as partidas da rodada atual
        url_partidas = f'https://api.cartolafc.globo.com/partidas/{rodada_atual}'
        
        # Tentativa de obter as partidas da rodada atual
        response = requests.get(url_partidas, headers=headers)
        response.raise_for_status()
        
        partidas = response.json()['partidas']
        
        # Nome do arquivo de saída
        nome_arquivo = f'jogos_da_rodada_{rodada_atual}.txt'
        
        # Abrir o arquivo para escrita
        with open(nome_arquivo, 'w', encoding='utf-8') as file:
            # Itera sobre as partidas e escreve as informações no arquivo
            for partida in partidas:
                time_casa_id = str(partida['clube_casa_id'])
                time_visitante_id = str(partida['clube_visitante_id'])
                time_casa = nome_do_time_por_id(clubes, time_casa_id)
                time_visitante = nome_do_time_por_id(clubes, time_visitante_id)
                data_hora = partida['partida_data']
                estadio = partida['local']
                placar_casa = partida['placar_oficial_mandante']
                placar_visitante = partida['placar_oficial_visitante']
                
                # Verifica se a partida já ocorreu
                if partida_ocorreu(placar_casa, placar_visitante):
                    placar = f"{placar_casa}  x  {placar_visitante}"
                else:
                    placar = "x"

                # Formatação das informações da partida
                file.write(f"{time_casa} {placar} {time_visitante}\n")
                if partida.get('valida') == True:
                    file.write(f"{formatar_data_hora(data_hora)}\n")
                    file.write(f"Estádio: {estadio}\n")
                else:
                    file.write('ESTA PARTIDA NÃO É VÁLIDA PARA A RODADA\n')
                file.write('\n')  # Linha em branco entre partidas
        
        # Mover o arquivo para a pasta da rodada atual dentro da pasta "Rodadas"
        shutil.move(nome_arquivo, os.path.join(caminho_completo_pasta, nome_arquivo))
        
    else:
        print('Não foi possível obter a rodada atual.')
    
except requests.exceptions.RequestException as e:
    print(f'Erro na solicitação: {e}')
except ValueError as e:
    print(f'Erro ao analisar a resposta JSON: {e}')