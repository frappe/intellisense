import os
from pygls.types import (
	Location,
	Position,
	Range,
	TextDocumentPositionParams,
)
from pygls.uris import from_fs_path
from .server import FrappeLanguageServer, get_config


def get_definitions(ls: FrappeLanguageServer, params: TextDocumentPositionParams):
	document = ls.workspace.get_document(params.textDocument.uri)

	if document.path.endswith("patches.txt"):
		return get_method_definition_for_patch(ls, params)


def get_method_definition_for_patch(
	ls: FrappeLanguageServer, params: TextDocumentPositionParams
):
	config = get_config()
	document = ls.workspace.get_document(params.textDocument.uri)
	line = document.lines[params.position.line]
	# remove new line and whitespaces
	line = line.strip()
	# remove comment
	line = line.split("#", 1)[0].strip()

	if line.startswith("execute:"):
		return

	module_path = line.replace(".", "/")
	app_name = module_path.split("/", 1)[0]
	file_path = os.path.join(
		config.frappe_bench_dir, "apps", app_name, module_path + ".py"
	)
	uri = from_fs_path(file_path)

	target_document = ls.workspace.get_document(uri)

	line_number = 0
	for line in target_document.lines:
		if "def execute():" in line:
			break
		line_number += 1

	link = Location(uri, Range(Position(line_number, 0), Position(line_number, 10)))
	return link
