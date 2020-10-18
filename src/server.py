from pygls.features import COMPLETION
from pygls.server import LanguageServer
from pygls.types import CompletionItem, CompletionList, CompletionParams

server = LanguageServer()

@server.feature(COMPLETION, trigger_characters=[','])
def completions(params):
    """Returns completion items."""
    return CompletionList(False, [
        CompletionItem('"'),
        CompletionItem('['),
        CompletionItem(']'),
        CompletionItem('{'),
        CompletionItem('}')
    ])

server.start_tcp('localhost', 8080)
