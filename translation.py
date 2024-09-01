import translators as ts

print("Start translating...")

to_translate = open("output.txt", "r").read()

print(ts.translate_text(to_translate, "baidu", "en", "pl"))
