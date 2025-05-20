import random
import json
import pickle
import numpy as np
import nltk
import re
import os
from datetime import datetime
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
from conexion import cursor, conn
from rapidfuzz import process, fuzz

# Descargar 'punkt' si no está disponible
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

lemmatizer = WordNetLemmatizer()

# Cargar intents
if not os.path.exists('intents_spanish.json'):
    raise FileNotFoundError("❌ El archivo intents_spanish.json no se encontró.")

with open('intents_spanish.json', 'r', encoding='utf-8') as file:
    intents = json.load(file)

words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_model.h5')
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Cargar productos desde la BD
cursor.execute("SELECT id_producto, nombre_producto FROM productos;")
productos_db = cursor.fetchall()
nombres_db = [nombre.lower() for _, nombre in productos_db]

# --- Funciones NLP ---

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return [{'intent': classes[r[0]], 'probability': str(r[1])} for r in results]

def get_response(intents_list, intents_json, mensaje_usuario=None):
    if not intents_list:
        return "Lo siento, no entendí eso."

    if mensaje_usuario:
        for intent in intents_list:
            if intent["intent"] == "registrar_venta_productos":
                return ejecutar_registro_venta(mensaje_usuario)
            elif intent["intent"] == "consultar_productos_a_vencer":
                return consultar_materia_prima_por_vencer(mensaje_usuario)
            elif intent["intent"] == "registrar_fecha_vencimiento":
                return registrar_fecha_vencimiento_desde_mensaje(mensaje_usuario)

    tag = intents_list[0]["intent"]
    for i in intents_json["intents"]:
        if i["tag"] == tag:
            return random.choice(i["responses"])

    return "Lo siento, no entendí eso."

# --- Funciones auxiliares ---

def extraer_productos_usuario(mensaje):
    mensaje = mensaje.lower().replace(" y ", ",").replace(".", "")
    numeros_texto = {
        "un": "1", "una": "1", "dos": "2", "tres": "3", "cuatro": "4",
        "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10"
    }
    for palabra, num in numeros_texto.items():
        mensaje = re.sub(rf"\\b{palabra}\\b", num, mensaje)

    patron = r"(\d+)\s+([\wáéíóúñ\s]+?)(?=,|$)"
    matches = re.findall(patron, mensaje)
    productos_final = [(int(c), n.strip()) for c, n in matches]

    correcciones = {
        "cafe amricano carajillo": "café americano carajillo",
        "frape moka": "frappes moka",
        "mojto cubano": "mojito cubano",
        "capuccino": "cappuccino"
    }
    productos_final = [(cantidad, correcciones.get(nombre, nombre)) for cantidad, nombre in productos_final]
    return productos_final

def obtener_id_producto(nombre_producto):
    mejor = process.extractOne(nombre_producto.lower(), nombres_db, scorer=fuzz.token_sort_ratio)
    if mejor and mejor[1] >= 80:
        match_name = mejor[0]
        for id_prod, nombre in productos_db:
            if nombre.lower() == match_name:
                return id_prod
    return None

# --- Función principal para registrar ventas ---

def ejecutar_registro_venta(mensaje):
    print(f"DEBUG - Mensaje recibido para venta: {mensaje}")
    productos = extraer_productos_usuario(mensaje)
    print(f"DEBUG - Productos extraidos: {productos}")
    
    if not productos:
        return "⚠️ No se pudieron extraer los productos correctamente."

    ids, cantidades, errores = [], [], []
    for cantidad, nombre in productos:
        producto_id = obtener_id_producto(nombre)
        if producto_id:
            ids.append(producto_id)
            cantidades.append(cantidad)
        else:
            errores.append(nombre)

    print(f"DEBUG - IDs productos: {ids}, Cantidades: {cantidades}, Errores: {errores}")

    if not ids:
        return "⚠️ No se registraron productos válidos para la venta."

    try:
        cursor.execute("SELECT registrar_venta_productos_formulario(%s, %s);", (ids, cantidades))
        resultado = cursor.fetchone()
        conn.commit()
        print(f"DEBUG - Resultado función SQL: {resultado}")
        respuesta = resultado[0] if resultado else "⚠️ No se pudo registrar la venta."
    except Exception as e:
        conn.rollback()
        print(f"DEBUG - Error en SQL: {e}")
        respuesta = f"❌ Error al registrar la venta: {e}"

    if errores:
        respuesta += "\n⚠️ No se encontraron los siguientes productos: " + ", ".join(errores)

    return respuesta


# --- Funciones para otros intents ---

def consultar_materia_prima_por_vencer(mensaje_usuario=None, dias_default=30):
    try:
        dias = dias_default
        if mensaje_usuario:
            match = re.search(r"(\d{1,3})\s*d[ií]as?", mensaje_usuario.lower())
            if match:
                dias = int(match.group(1))

        cursor.execute("SELECT * FROM materia_prima_por_vencer(%s);", (dias,))
        resultados = cursor.fetchall()

        if not resultados:
            return f"No hay materias primas que vencen en los próximos {dias} días."

        respuesta = f"🧾 Materias primas que vencen en los próximos {dias} días:\n"
        for fila in resultados:
            id_materia, nombre, fecha_venc, stock, dias_rest = fila
            respuesta += f"- {nombre} (vence el {fecha_venc}, stock: {stock}, en {dias_rest} días)\n"

        return respuesta
    except Exception as e:
        return f"⚠️ Error al consultar productos por vencer: {e}"

def registrar_fecha_vencimiento_desde_mensaje(mensaje):
    try:
        mensaje = mensaje.lower().strip()

        patron = r"registrar(?:\s+que)?\s+(?:el\s+)?([\w\sáéíóúñ]+?)\s+se\s+vence\s+el\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        match = re.search(patron, mensaje)

        if not match:
            patron_alt = r"registrar\s+([\w\sáéíóúñ]+?)\s+vence\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            match = re.search(patron_alt, mensaje)
            if not match:
                return "⚠️ El formato debe ser: registrar que (nombre materia prima) se vence el (fecha)."

        nombre = match.group(1).strip()
        fecha_texto = match.group(2).replace("/", "-")
        fecha = datetime.strptime(fecha_texto, "%d-%m-%Y").date()

        cursor.execute("SELECT id_materia FROM materia_prima WHERE LOWER(nombre_materia) = %s;", (nombre.lower(),))
        result = cursor.fetchone()
        if not result:
            return f"⚠️ No se encontró la materia prima '{nombre}'."

        id_materia = result[0]
        cursor.execute("SELECT registrar_fecha_vencimiento(%s, %s);", (id_materia, fecha))
        resultado = cursor.fetchone()
        conn.commit()
        return resultado[0] if resultado else "⚠️ No se pudo registrar la fecha."
    except Exception as e:
        conn.rollback()
        return f"⚠️ Error al registrar fecha de vencimiento: {e}"
