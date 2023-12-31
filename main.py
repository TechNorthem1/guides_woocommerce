import pyttsx3
from fpdf import FPDF
import barcode
from barcode.writer import ImageWriter
import requests
import subprocess
import platform


# Inicializa el motor de texto a voz
engine = pyttsx3.init()


# Configura la API de WooCommerce
def all_orders(date_init, date_end):
    headers = {
        "Authorization": "Basic Y2tfNjBjYWMzNjg4Njk5YmRiYTczOTU0ZmU1MDhkNjczYzk1YThhZGU3ZTpjc19hMDdiYWMxMTMyNWM3NjljNDQxNmRjYWY4OWIzYWI2YjdmNzEyMGQz"
    }
    response = requests.request("GET", f"https://titandecko.com.co/wp-json/wc/v3/orders?per_page=100&after={date_init}T00:00:00&before={date_end}T23:59:59&order=asc", headers=headers)
    return response

# Función para obtener pedidos nuevos desde WooCommerce
def obtener_pedidos_nuevos(date_init, date_end):
    try:
        response = all_orders(date_init, date_end).json()
        return response
    except Exception as e:
        print(f"Error al obtener los pedidos: {e}")
        return []

# Función para leer el último ID de pedido notificado
def leer_ultimo_pedido_notificado():
    try:
        with open('ultimo_pedido.txt', 'r') as file:
            ultimo_id = file.read().strip()
            return int(ultimo_id) if ultimo_id else 0
    except FileNotFoundError:
        return 0

# Función para guardar el último ID de pedido notificado
def guardar_ultimo_pedido_notificado(pedido_id):
    with open('ultimo_pedido.txt', 'w') as file:
        file.write(str(pedido_id))

# Función para generar un código de barras
def generar_codigo_barras(numero_pedido):
    EAN = barcode.get_barcode_class('ean13')
    ean = EAN(str(numero_pedido).zfill(12), writer=ImageWriter())
    archivo_codigo_barras = f"barcode_{numero_pedido}"
    ean.save(f"codes_of_bars/{archivo_codigo_barras}")
    return archivo_codigo_barras

def replace_unsupported_characters(text):
    # Diccionario de reemplazo para caracteres no soportados
    replacements = {
        u'\u2013': '-',  # en dash
        u'\u2014': '--', # em dash
        u'\u2018': "'",  # left single quotation mark
        u'\u2019': "'",  # right single quotation mark
        u'\u201c': '"',  # left double quotation mark
        u'\u201d': '"',  # right double quotation mark
        # Agregar más reemplazos si es necesario
    }
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    return text

def imprimir_pdf(archivo_pdf):
    try:
        # Detectar el sistema operativo
        sistema = platform.system()

        if sistema == 'Windows':
            # En Windows, se puede usar el comando 'print' para enviar el archivo a la impresora predeterminada
            subprocess.run(['print', '/d:"%printer%"', archivo_pdf], shell=True)
        elif sistema == 'Darwin':
            # En macOS, se puede usar el comando 'lpr' para enviar el archivo a la impresora predeterminada
            subprocess.run(['lpr', archivo_pdf])
        else:
            # En Linux, se puede usar el comando 'lpr' igualmente para enviar el archivo a la impresora predeterminada
            subprocess.run(['lpr', archivo_pdf])
    except Exception as e:
        print(f"Ocurrió un error al intentar imprimir el PDF: {e}")

# Función para generar el PDF del pedido
def generar_pdf(order):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Incluir logo de la empresa
    pdf.image('logo/path_al_logo.png', 10, 8, 33)
    
    # Añadir información del pedido
    pdf.cell(0, 10, f"Pedido N°: {order['id']}", ln=True)
    
    # Generar y añadir el código de barras
    archivo_codigo_barras = generar_codigo_barras(order['id'])
    pdf.image(f"codes_of_bars/{archivo_codigo_barras}.png", x=10, y=30, w=50)
    pdf.ln(20) 

    # Añadir información de productos del pedido
    for item in order['line_items']:
        pdf.cell(0, 10, f"Producto: {replace_unsupported_characters(item['name'])} - Cantidad: {replace_unsupported_characters(str(item['quantity']))} - Precio: {replace_unsupported_characters(str(item['price']))}", ln=True)
    
    # Guardar PDF
    archivo_pdf = f"orders/pedido_{order['id']}.pdf"
    pdf.output(archivo_pdf)
    return archivo_pdf

# Función principal que ejecuta el script
def main(date_init, date_end):
    ultimo_pedido_id = leer_ultimo_pedido_notificado()
    pedidos = obtener_pedidos_nuevos(date_init, date_end)
    
    for pedido in pedidos:
        pedido_id = pedido['id']
        if pedido_id > ultimo_pedido_id:
            engine.say("Tienes un nuevo pedido.")
            engine.runAndWait()
            archivo_pdf = generar_pdf(pedido)
            imprimir_pdf(archivo_pdf)
            print(f"PDF generado para el pedido: {archivo_pdf}")
            guardar_ultimo_pedido_notificado(pedido_id)

if __name__ == "__main__":
    date_init = input("Ingresar fecha inicial con el formato 2023-11-29: ")
    date_end = input("Ingresar fecha final con el formato 2023-11-29: ")
    while True:
        main(date_init, date_end)