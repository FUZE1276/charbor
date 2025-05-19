import pickle

with open('chatbot_model.h5', 'rb') as file:
    words = pickle.load(file)

with open('words.txt', 'w', encoding='utf-8') as out_file:
    for word in words:
        out_file.write(f"{word}\n")

print("Archivo words.txt creado con éxito.")
