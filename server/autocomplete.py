import re
from .server import get_config
from pygls.workspace import Document
import jedi
from pygls.lsp.types import (
	CompletionParams,
	Position,
)
from .utils import guess_doctype


def get_document_autocompletion_items(ls, params: CompletionParams):
	config = get_config()
	document: Document = ls.workspace.get_document(params.text_document.uri)
	position_before_dot = Position(line=params.position.line, character=params.position.character - 1)
	word_before_dot = document.word_at_position(position_before_dot)

	# autocomplete "self." in class controllers
	if word_before_dot == "self":
		doctype = guess_doctype(document)
		if not doctype:
			return
		return config.doctype_intellisense(doctype).get()

	environment = config.get_jedi_environment()
	script = jedi.Script(code=document.source, path=document.path, environment=environment)

	# autocomplete "doc." in python files
	references = script.get_references(
		position_before_dot.line + 1, position_before_dot.character
	)

	for reference in references:
		get_doc_pattern = r"=\s*frappe\.get_doc\([\"']([\w ]+)['\"],"

		match = re.search(get_doc_pattern, reference.description)
		if (
			reference.type == "statement" and match and reference.line < params.position.line + 1
		):
			doctype = match.group(1)
			return config.doctype_intellisense(doctype).get(with_class_methods=True)


def scrub(txt):
	return txt.replace(" ", "_").replace("-", "_").lower()
