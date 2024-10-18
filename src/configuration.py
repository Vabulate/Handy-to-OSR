import yaml
with open("config.yaml", "r", encoding="utf-8") as file:
    configuration = yaml.safe_load(file)['configs']