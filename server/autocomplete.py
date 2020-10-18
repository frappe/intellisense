import io
import json
import re
import glob
from os import path
from pydoc import doc
from pygls.workspace import Document
import jedi
import os
from pygls.types import (
	CompletionItem,
	CompletionItemKind,
	CompletionList,
	CompletionParams,
	Position,
)
from .utils import find_frappe_bench_dir

doctype_path_meta_map = {}
doctype_name_meta_map = {}
jedi_environment = None


def get_document_autocompletion_items(ls, params: CompletionParams):

	document: Document = ls.workspace.get_document(params.textDocument.uri)
	position_before_dot = Position(params.position.line, params.position.character - 1)
	word = document.word_at_position(position_before_dot)

	environment = get_jedi_environment(ls)
	script = jedi.Script(code=document.source, path=document.path, environment=environment)

	if word == "self":
		context = script.get_context(params.position.line + 1, params.position.character)
		doctype_meta = get_doctype_meta(document.path)
		if not doctype_meta:
			return

		current_name = context
		while current_name.type != "class":
			current_name = current_name.parent()

		if ".doctype." in current_name.full_name:
			return get_completion_items_for_doctype(doctype_meta)

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
			doctype_meta = get_doctype_meta_by_name(doctype)
			return get_completion_items_for_doctype(doctype_meta)


def get_completion_items_for_doctype(doctype_meta):
	completion_items = []
	for df in doctype_meta["fields"]:
		if df["fieldtype"] in ["Section Break", "Column Break"]:
			continue

		c = CompletionItem(
			df["fieldname"],
			CompletionItemKind.Field,
			detail=get_docfield_details(df),
			sort_text="a",
		)
		completion_items.append(c)

	return CompletionList(False, completion_items)


def get_doctype_meta(filepath):
	if filepath not in doctype_path_meta_map:
		name, _ = os.path.splitext(filepath)
		doctype_json = get_file_contents(name + ".json")
		try:
			if doctype_json:
				doctype_meta = json.loads(doctype_json)
				if doctype_meta["doctype"] == "DocType":
					doctype_path_meta_map[filepath] = doctype_meta
					doctype_name_meta_map[doctype_meta["name"]] = doctype_meta
		except json.decoder.JSONDecodeError:
			pass
		if not doctype_path_meta_map.get(filepath):
			doctype_path_meta_map[filepath] = None

	return doctype_path_meta_map.get(filepath)


def get_doctype_meta_by_name(doctype):
	if doctype not in doctype_name_meta_map:
		scrubbed = scrub(doctype)
		frappe_bench_dir = find_frappe_bench_dir()
		if frappe_bench_dir:
			paths = glob.glob(
				path.join(frappe_bench_dir, "apps", "**", "doctype", scrubbed, scrubbed + ".json"),
				recursive=True,
			)
			if paths:
				doctype_name_meta_map[doctype] = get_doctype_meta(paths[0])

	return doctype_name_meta_map.get(doctype)


def get_docfield_details(df, join_by="\n"):
	field_meta = [df.get("label") or ""]
	fieldtype = df["fieldtype"]
	field_meta.append(f"Fieldtype: {fieldtype}")

	description = df.get("description")
	if description:
		field_meta.append(f"Description: ${description}")

	options = df.get("options")
	if fieldtype == "Select" and options:
		select_options = ", ".join(options.split("\n"))
		field_meta.append(f"Options: {select_options}")
	elif options:
		field_meta.append(f"Options: {options}")

	return join_by.join(field_meta)


def get_file_contents(filepath):
	if os.path.exists(filepath):
		with io.open(filepath, "r") as f:
			return f.read()


def get_jedi_environment(ls):
	global jedi_environment

	if not jedi_environment:
		frappe_bench_dir = find_frappe_bench_dir(ls)
		jedi_environment = jedi.create_environment(path.join(frappe_bench_dir, "env"))

	return jedi_environment


def scrub(txt):
	return txt.replace(" ", "_").replace("-", "_").lower()
