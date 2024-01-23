from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

# Defina o caminho para os arquivos Excel dos setores
planilhas_path = {
    'Mercado_Pago': 'hub-vouchers-main\mp-vouchers.xlsx',
    'Mercado_Livre': 'hub-vouchers-main\ml-vouchers.xlsx',
    'Diretoria': 'hub-vouchers-main\diretoria-vouchers.xlsx'
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

@app.route('/')
def index():
    quantidade_disponivel = carregar_quantidade_disponivel()
    return render_template('index.html', quantidade_disponivel=quantidade_disponivel)

@app.route('/retirar', methods=['POST'])
def retirar_vouchers():
    setor = request.form.get('setor')
    quantidade_str = request.form.get('quantidade')
    aceitar_termos = request.form.get('aceitar-termos')

    # Verifique se a caixa de seleção de aceitar termos foi marcada
    if aceitar_termos != 'on':
        return jsonify({'error': 'Você deve aceitar os Termos e Condições para retirar vouchers.'}), 400

    try:
        quantidade = int(quantidade_str)

        # Verifique se o setor selecionado é válido
        if setor not in planilhas_path:
            return jsonify({'error': 'Setor inválido.'}), 400

        planilha_path = planilhas_path[setor]

        # Lê a planilha do setor selecionado
        try:
            df = pd.read_excel(planilha_path)

            # Filtra os vouchers disponíveis
            vouchers_disponíveis = df[df['Status'] == 'Disponível']

            if quantidade <= 0:
                return jsonify({'error': 'A quantidade deve ser maior que zero.'}), 400

            if quantidade > vouchers_disponíveis.shape[0]:
                return jsonify({'error': 'Não há vouchers suficientes disponíveis na planilha do setor {}.'.format(setor)}), 400

            # Seleciona os vouchers disponíveis para retirada
            vouchers_retirados = vouchers_disponíveis.head(quantidade)

            # Marca os vouchers retirados como "Usados"
            df.loc[vouchers_retirados.index, 'Status'] = 'Usado'

            # Salva a planilha Excel atualizada
            df.to_excel(planilha_path, index=False)

            # Recolha os códigos de voucher retirados
            codigos_voucher = vouchers_retirados['Códigos de Voucher'].tolist()

            # Renderize a página codigos.html com os códigos de voucher
            return render_template('codigos.html', codigos_voucher=codigos_voucher)

        except Exception as e:
            return jsonify({'error': 'Erro ao processar a planilha do setor {}: {}'.format(setor, str(e))}), 500

    except ValueError:
        return jsonify({'error': 'A quantidade deve ser um número inteiro válido.'}), 400

if __name__ == '__main__':
    app.run(debug=True)
