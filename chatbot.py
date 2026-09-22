import ollama

print("🤖 WAYVO Chatbot")
print("Type 'exit' to quit.\n")

messages = [
    {
        "role": "system",
        "content": """You are WAYVO, a friendly, helpful, and natural AI assistant.
Your name is WAYVO.
Speak in simple, clear language.
Be conversational and warm, not robotic.
Keep answers concise unless the user asks for details.
Remember the conversation and use previous messages when relevant."""
    }
]

while True:
    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("WAYVO: Bye! 👋")
        break

    messages.append({
        "role": "user",
        "content": user_message
    })

    response = ollama.chat(
        model="llama3.2",
        messages=messages
    )

    assistant_message = response["message"]["content"]

    print("WAYVO:", assistant_message)

    messages.append({
        "role": "assistant",
        "content": assistant_message
    })