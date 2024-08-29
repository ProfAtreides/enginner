import translators as ts

to_translate = open("output.txt", "r").read()

print(to_translate)

print(ts.translate_text(to_translate, "baidu", "en", "pl"))
