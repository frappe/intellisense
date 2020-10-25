from pygls.features import (
	COMPLETION,
	DEFINITION,
	TEXT_DOCUMENT_DID_OPEN,
	TEXT_DOCUMENT_DID_SAVE,
)
from pygls.server import LanguageServer
from pygls.types import (
	CompletionParams,
	DidOpenTextDocumentParams,
	DidSaveTextDocumentParams,
	TextDocumentPositionParams,
)
from .config import IntellisenseConfig


class FrappeLanguageServer(LanguageServer):
	CONFIGURATION_SECTION = "frappe-intellisense"

	def __init__(self):
		super().__init__()


frappe_server = FrappeLanguageServer()
config = IntellisenseConfig()


@frappe_server.command("setupFrappeIntellisense")
def setup_frappe_intellisense(ls: FrappeLanguageServer, *args):
	config.setup(ls)


@frappe_server.feature(COMPLETION, trigger_characters=["."])
def completions(ls: FrappeLanguageServer, params: CompletionParams = None):
	"""Returns completion items."""
	from .autocomplete import get_document_autocompletion_items

	config.setup(ls)
	if config.not_frappe():
		return

	return get_document_autocompletion_items(ls, params)


@frappe_server.feature(DEFINITION)
def definition(ls: FrappeLanguageServer, params: TextDocumentPositionParams):
	from .definition import get_definitions

	config.setup(ls)
	if config.not_frappe():
		return

	definitions = get_definitions(ls, params)
	return definitions


@frappe_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: DidSaveTextDocumentParams):
	"""Text document did save notification."""

	config.setup(ls)
	if config.not_frappe():
		return

	send_diagnostics(ls, params)
	config.update_doctype_intellisense(params)


# @server.feature(TEXT_DOCUMENT_DID_CLOSE)
# def did_close(server: FrappeLanguageServer, params: DidCloseTextDocumentParams):
# 	"""Text document did close notification."""
# 	server.show_message("Text Document Did Close")


@frappe_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
	"""Text document did open notification."""

	config.setup(ls)
	if config.not_frappe():
		return

	send_diagnostics(ls, params)


def send_diagnostics(ls, params):
	from .diagnostics import get_translation_diagnostics

	diagnostics = get_translation_diagnostics(ls, params)
	ls.publish_diagnostics(params.textDocument.uri, diagnostics)


def get_config():
	return config
