# exceptions.py
class ParserFindTagException(Exception):
    '''Вызывается, когда парсер не может найти тег.'''
    pass


class ParserFindUrlException(Exception):
    '''Вызывается, когда парсер не смог найти в тэгах
    блок со ссылками на документацию'''
