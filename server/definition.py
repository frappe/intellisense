import os
import re
from pygls.lsp.types import (
	Location,
	Position,
	Range,
	TextDocumentPositionParams,
)
from pygls.uris import from_fs_path
from .server import FrappeLanguageServer, get_config


def get_definitions(ls: FrappeLanguageServer, params: TextDocumentPositionParams):
	document = ls.workspace.get_document(params.text_document.uri)

	if document.path.endswith("patches.txt"):
		return get_method_definition_for_patch(ls, params)

	# module path strings like "frappe.frappe.core.doctype.todo.todo"
	line = document.lines[params.position.line]
	module_path_pattern = r"(['\"])(\w+(\.\w+)+)\1"
	match = re.search(module_path_pattern, line)
	if match:
		module_path = match.group(2)
		return get_location_from_module_path(ls, module_path)


def get_method_definition_for_patch(
	ls: FrappeLanguageServer, params: TextDocumentPositionParams
):
	document = ls.workspace.get_document(params.text_document.uri)
	line = document.lines[params.position.line]
	# remove new line and whitespaces
	line = line.strip()
	# remove comment
	line = line.split("#", 1)[0].strip()

	if line.startswith("execute:"):
		return

	line = f"{line}.execute"
	return get_location_from_module_path(ls, line)


def get_location_from_module_path(ls, module_path):
	config = get_config()
	module_path, method = module_path.rsplit(".", 1)

	module_path = module_path.replace(".", "/")
	app_name = module_path.split("/", 1)[0]
	file_path = os.path.join(
		config.frappe_bench_dir, "apps", app_name, module_path + ".py"
	)
	if not os.path.exists(file_path):
		return

	uri = from_fs_path(file_path)
	target_document = ls.workspace.get_document(uri)

	line_number = 0
	for line in target_document.lines:
		if f"def {method}(" in line:
			break
		line_number += 1

	range = Range(
		start=Position(line=line_number, character=0),
		end=Position(line=line_number, character=len(method) + 4),
	)
	link = Location(uri=uri, range=range)
	return link
