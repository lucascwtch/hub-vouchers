# Importe a classe Flask e outros módulos necessários
from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import datetime

# Crie uma instância do Flask
app = Flask(__name__)

# Defina o caminho para os arquivos Excel dos setores
planilhas_path = {
    'Mercado_Pago': 'mp-vouchers.xlsx',
    'Mercado_Livre': 'ml-vouchers.xlsx',
    'Diretoria': 'diretoria-vouchers.xlsx',
    'Claro': 'claro-vouchers.xlsx',
    'Vivo': 'vivo-vouchers.xlsx',
    'Kroton': 'kroton-vouchers.xlsx'
}

# Função para carregar a quantidade de vouchers disponíveis para cada setor
def carregar_quantidade_disponivel():
    quantidade_disponivel = {}
    for setor, planilha_path in planilhas_path.items():
        try:
            df = pd.read_excel(planilha_path)
            quantidade_disponivel[setor] = df[df['Status'] == 'Disponível'].shape[0]
        except Exception as e:
            quantidade_disponivel[setor] = 0
    return quantidade_disponivel

def registrar_retirada(setor, quantidade, nome, cpf):
    try:
        app.logger.info('Nome e CPF recebidos: %s, %s', nome, cpf)
        planilha_path = planilhas_path[setor]
        df = pd.read_excel(planilha_path)

        # Filtra os vouchers disponíveis
        vouchers_disponíveis = df[df['Status'] == 'Disponível']

        app.logger.info('Quantidade Disponível: %d', vouchers_disponíveis.shape[0])

        if quantidade <= 0:
            return {'error': 'A quantidade deve ser maior que zero.'}, 400

        if quantidade > vouchers_disponíveis.shape[0]:
            return {'error': 'Não há vouchers suficientes disponíveis na planilha do setor {}.'.format(setor)}, 400

        # Seleciona os vouchers disponíveis para retirada
        vouchers_retirados = vouchers_disponíveis.head(quantidade)

        # Marca os vouchers retirados como "Usados"
        df.loc[vouchers_retirados.index, 'Status'] = 'Usado'

        # Adiciona informações de retirada (nome, CPF, data)
        retirado_por = f'{nome} (CPF: {cpf})'

        app.logger.info('Retirado Por: %s', retirado_por)

        # Converter 'None (CPF: None)' para uma string vazia ('') para evitar problemas de tipo
        retirado_por = retirado_por if (nome is not None) and (cpf is not None) else ''
        df.loc[vouchers_retirados.index, 'Retirado Por'] = retirado_por

        # Converter datetime.now() para uma string no formato desejado antes de atribuir
        data_retirada = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df.loc[vouchers_retirados.index, 'Data Retirada'] = data_retirada

        # Salva a planilha Excel atualizada
        df.to_excel(planilha_path, index=False)

        # Recolha os códigos de voucher retirados
        codigos_voucher = vouchers_retirados['Códigos de Voucher'].tolist()

        app.logger.info('Códigos de Voucher: %s', codigos_voucher)

        # Modifique a linha de retorno da função para retornar um dicionário
        return {'codigos_voucher': codigos_voucher, 'retirado_por': retirado_por}

    except Exception as e:
        app.logger.error('Erro ao processar a planilha do setor %s: %s', setor, str(e))
        return {'error': 'Erro ao processar a planilha do setor {}: {}'.format(setor, str(e))}, 500


# Rota principal para renderizar a página inicial
@app.route('/')
def index():
    quantidade_disponivel = carregar_quantidade_disponivel()
    return render_template('index.html', quantidade_disponivel=quantidade_disponivel)

# Rota para retirar vouchers (submissão do formulário)
@app.route('/retirar', methods=['POST'])
def retirar_vouchers():
    setor = request.form.get('setor')
    quantidade_str = request.form.get('quantidade')
    aceitar_termos = request.form.get('aceitar-termos')
    nome = request.form.get('nome')
    cpf = request.form.get('cpf')

    app.logger.info('Setor: %s, Quantidade: %s, Aceitar Termos: %s, Nome: %s, CPF: %s', setor, quantidade_str, aceitar_termos, nome, cpf)

    # Verifique se a caixa de seleção de aceitar termos foi marcada
    if aceitar_termos != 'on':
        return jsonify({'error': 'Você deve aceitar os Termos e Condições para retirar vouchers.'}), 400

    app.logger.info('Antes de chamar registrar_retirada - Nome: %s, CPF: %s', nome, cpf)

    try:
        quantidade = int(quantidade_str)

        # Verifique se o setor selecionado é válido
        if setor not in planilhas_path:
            return jsonify({'error': 'Setor inválido.'}), 400

        # Valide o nome e CPF conforme necessário
        # ...

        app.logger.info('Depois de validar nome e CPF - Nome: %s, CPF: %s', nome, cpf)

        # Chame a função para registrar a retirada
        resultado = registrar_retirada(setor, quantidade, nome, cpf)

        # Verifique o resultado da operação
        if 'error' in resultado:
            return jsonify(resultado), resultado.get('status', 500)

        # Ajuste para lidar com casos em que resultado['codigos_voucher'] ou resultado['retirado_por'] podem ser None
        codigos_voucher = resultado['codigos_voucher'] if resultado and 'codigos_voucher' in resultado else []
        retirado_por = resultado['retirado_por'] if resultado and 'retirado_por' in resultado else ''


        # Verifique se há vouchers disponíveis
        if not codigos_voucher:
            return render_template('sem_vouchers.html', setor=setor)

        return render_template('codigos.html', codigos_voucher=codigos_voucher, retirado_por=retirado_por)

    except ValueError:
        return jsonify({'error': 'A quantidade deve ser um número inteiro válido.'}), 400


# Rota para coletar informações do usuário (exemplo adicional)
@app.route('/coletar_informacoes_usuario', methods=['POST'])
def coletar_informacoes_usuario():
    nome = request.form.get('nome')
    cpf = request.form.get('cpf')

    app.logger.info(f'Nome: {nome}, CPF: {cpf}')

    return jsonify({'success': True})

# Inicialize o aplicativo se este script for executado diretamente
if __name__ == '__main__':
    app.run(debug=True)
