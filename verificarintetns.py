import json

# Cargar el archivo JSON
with open("intents_spanish.json", "r", encoding="utf-8") as file:
    intents_data = json.load(file)

# Verificar intents sin "patterns"
intents_sin_patterns = []

for intent in intents_data["intents"]:
    if "patterns" not in intent:
        intents_sin_patterns.append(intent["tag"])

# Mostrar resultados
if intents_sin_patterns:
    print("⚠️ Los siguientes intents no tienen la clave 'patterns':")
    for tag in intents_sin_patterns:
        print(f"- {tag}")
else:
    print("✅ Todos los intents tienen la clave 'patterns'. ¡El JSON está bien estructurado!")