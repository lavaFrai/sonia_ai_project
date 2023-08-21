import yaml


class I18n:
    def __init__(self, lang='en-US'):
        with open("i18n/" + lang + '.yml', encoding='utf8') as f:
            self.data = yaml.load(f, Loader=yaml.FullLoader)

    def get_string(self, name):
        return self.data[name]
