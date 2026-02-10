import ollama

response = ollama.generate(
    model='deepseek-coder:6.7b',
    prompt='Explain what Python is in one sentence.'
)
print(response['response'])
