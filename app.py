from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
import fitz
import json

app = Flask(__name__)
CORS(app)

# Regex patterns
pattern1 = r'(?P<ID>\d+)\s+(?P<COD>\d+)(?P<DESCRIPTION>[^\d].*?)\s+(?P<QTD>\d+,\d+)(?P<UN>[A-Z]+)\s+(?P<VL_UN>\d+,\d+)\s+\((?P<VL_TR>[\d,-]+)\)\s+(?P<VL_ITEM>\d+,\d+)'
pattern2 = r'(?P<ID>\d+)\s+(?P<COD>\d+)\s+(?P<DESCRIPTION>.+?)\s+(?P<QTD>\d+,\d+)\s+(?P<UN>[A-Z]+)\s+(?P<VL_UN>\d+,\d+)\s+\((?P<VL_TR>[\d,-]+)\)\s+(?P<VL_ITEM>\d+,\d+)'

def contains_integer_between_1_and_100(s):
    """
    Verifica se a string contém um número inteiro entre 1 e 100
    que está isolado ou seguido de espaços/delimitadores.

    :param s: A string a ser analisada.
    :return: O número encontrado (se houver) ou None.
    """
    # Regex para encontrar números inteiros entre 1 e 100 isolados ou seguidos de espaços
    match = re.search(r'(?<!\d,)\b([1-9][0-9]?|100)\b(?!,\d)', s)
    if match:
        return int(match.group(1))
    return None

def extract_product_info(item_text):

    match = re.search(pattern1, item_text)

    # Processar os matches
    if match:
        return {
            'ID': match.group('ID'),
            'COD': match.group('COD'),
            'DESCRIPTION': match.group('DESCRIPTION').strip(),
            'QTD': match.group('QTD'),
            'UN': match.group('UN'),
            'VL_UN': match.group('VL_UN'),
            'VL_TR': match.group('VL_TR'),
            'VL_ITEM': match.group('VL_ITEM')}

    # Tente o segundo padrão
    match = re.search(pattern2, item_text)

    if match:
        return {
            'ID': match.group('ID'),
            'COD': match.group('COD'),
            'DESCRIPTION': match.group('DESCRIPTION').strip(),
            'QTD': match.group('QTD'),
            'UN': match.group('UN'),
            'VL_UN': match.group('VL_UN'),
            'VL_TR': match.group('VL_TR'),
            'VL_ITEM': match.group('VL_ITEM')}

    return None

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")

        expected = 0  # Começamos esperando o número 1
        product_info = []
        items = []

        for page in doc:
            text = page.get_text()    
            #print(text)

            # Quebrar o texto em linhas
            lines = text.split('\n')
            
            for line in lines:

                #print(line)
                number = int(contains_integer_between_1_and_100(line)) - 1 if contains_integer_between_1_and_100(line) is not None else None
                #print(number, ' - ', expected)
                if number == expected:
                    expected += 1
                    
                    if product_info:
                        #Aqui temos as informações do produto
                        string_result = ' '.join(product_info)
                        item = extract_product_info(string_result)
                        #print(item, "\n")
                        items.append(item)
                    product_info = []
                    product_info.append(line)
                if number is None:
                    product_info.append(line)
        string_result = ' '.join(product_info)
        item = extract_product_info(string_result)
        items.append(item)

        # Converte o array de objetos para uma string JSON
        json_data = json.dumps(items, indent=2)
        return jsonify(json.loads(json_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':    
    port = int(os.environ.get('PORT', 5000))  # Usa a porta fornecida ou 5000 como padrão
    app.run(host='0.0.0.0', port=port)