import streamlit as st
from chatbot import predict_class, get_response, intents  

st.set_page_config(page_title="Asistente de Base de Datos", page_icon="🧠")

st.title("Asistente de la base de datos ☑🚀")

# ✅ Inicializar sesión de conversación
if "messages" not in st.session_state:
    st.session_state.messages = []
if "first_message" not in st.session_state:
    st.session_state.first_message = True

# ✅ Mostrar historial de conversación
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ✅ Mensaje de bienvenida (una sola vez)
if st.session_state.first_message:
    bienvenida = "Hola, ¿cómo puedo ayudarte?"
    with st.chat_message("assistant"):
        st.markdown(bienvenida)
    st.session_state.messages.append({"role": "assistant", "content": bienvenida})
    st.session_state.first_message = False

# ✅ Entrada del usuario y procesamiento de intent
if prompt := st.chat_input("¿Cómo puedo ayudarte?"):
    # Mostrar entrada del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 🔍 Intent detection
    detected_intents = predict_class(prompt)
    print(f"🔍 Intents detectados: {detected_intents}")

    # ✅ Generar respuesta usando la lógica del chatbot
    if not detected_intents:
        response = "⚠️ No se detectó ninguna acción válida. Intenta reformular tu mensaje."
    else:
        response = get_response(detected_intents, intents, mensaje_usuario=prompt)

    # Mostrar respuesta del chatbot
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
