from deep_translator import DeeplTranslator
import pandas as pd

# Load API token
df = pd.read_csv('api_token.csv')
api_key = df['deepl'].iloc[0]

print(api_key)

print("Start translating...")

to_translate = open("output.txt", "r").read()

print(DeeplTranslator(api_key=api_key, source='english', target='polish').translate(to_translate))
