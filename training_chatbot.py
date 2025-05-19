import nltk
from nltk.stem import WordNetLemmatizer
import json
import pickle
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import SGD
from tensorflow.keras.optimizers.schedules import ExponentialDecay
import random
import os

for archivo in ["chatbot_model.h5", "words.pkl", "classes.pkl"]:
    if os.path.exists(archivo):
        os.remove(archivo)
        print(f"🧹 Archivo eliminado: {archivo}")


# Descargar recursos de NLTK si no están
nltk.download('punkt')
nltk.download('wordnet')

# ✅ Cargar el archivo de intents
INTENTS_FILE = 'intents_spanish.json'
if not os.path.exists(INTENTS_FILE):
    raise FileNotFoundError(f"❌ Archivo no encontrado: {INTENTS_FILE}")

with open(INTENTS_FILE, 'r', encoding='utf-8') as file:
    intents = json.load(file)

lemmatizer = WordNetLemmatizer()
words = []
classes = []
documents = []
ignore_words = ['?', '!', '.', ',']

# ✅ Procesar intents
for intent in intents['intents']:
    if "patterns" in intent and isinstance(intent["patterns"], list) and "tag" in intent:
        for pattern in intent["patterns"]:
            w = nltk.word_tokenize(pattern)
            words.extend(w)
            documents.append((w, intent["tag"]))
            if intent["tag"] not in classes:
                classes.append(intent["tag"])
    else:
        print(f"⚠️ Estructura inválida en intent: {intent}")

# ✅ Lematizar y limpiar palabras
words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
words = sorted(set(words))
classes = sorted(set(classes))

# ✅ Guardar palabras y clases
pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

print(f"🔍 Total de intents: {len(classes)}")
print(f"🔍 Vocabulario total: {len(words)}")

# ✅ Verificar distribución de tags
tag_counts = {tag: 0 for tag in classes}
for _, tag in documents:
    tag_counts[tag] += 1
print(f"📊 Distribución de patrones por intent:\n{tag_counts}")

# ✅ Crear datos de entrenamiento
training = []
output_empty = [0] * len(classes)

for pattern_words, tag in documents:
    bag = []
    pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_words]
    bag = [1 if word in pattern_words else 0 for word in words]

    output_row = output_empty[:]
    output_row[classes.index(tag)] = 1

    training.append([bag, output_row])

random.shuffle(training)
train_x = np.array([row[0] for row in training])
train_y = np.array([row[1] for row in training])

# ✅ Crear el modelo
model = Sequential()
model.add(Dense(256, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

# ✅ Optimizador con decaimiento
lr_schedule = ExponentialDecay(
    initial_learning_rate=0.01,
    decay_steps=10000,
    decay_rate=0.9
)
sgd = SGD(learning_rate=lr_schedule, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# ✅ Entrenamiento
hist = model.fit(train_x, train_y, epochs=300, batch_size=5, verbose=1)

# ✅ Guardar modelo
model.save('chatbot_model.h5', hist)

print(f"✅ Entrenamiento completado con precisión final: {hist.history['accuracy'][-1]:.2f}")
print("✅ Modelo guardado como chatbot_model.h5")
