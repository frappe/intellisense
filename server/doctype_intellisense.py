import os
import jedi
from jedi.api.classes import Completion
from pygls.types import (
	CompletionItem,
	CompletionItemKind,
	CompletionList,
	InsertTextFormat,
	MarkupContent,
)


class DocTypeIntellisense:
	def __init__(self, doctype, meta, folder, config):
		self.doctype = doctype
		self.meta = meta
		self.folder = folder
		self.frappe_bench_path = config.frappe_bench_dir
		self.config = config
		self.fields = []
		self.build_fields()

	def get(self, with_class_methods=False):
		items = []

		fieldnames = []
		for df in self.fields:
			fieldname = df["fieldname"]
			fieldnames.append(fieldname)
			c = CompletionItem(
				label=fieldname,
				kind=CompletionItemKind.Variable,
				detail=fieldname,
				documentation=MarkupContent(kind="markdown", value=self.get_docfield_details(df)),
				sort_text="a",
				insert_text=fieldname,
				insert_text_format=InsertTextFormat.PlainText,
			)
			items.append(c)

		if with_class_methods:
			self.build_jedi_completions()
			for completion in self.jedi_completions:
				if completion.name in fieldnames:
					continue
				items.append(lsp_completion_item(completion, self.module_name))

		return CompletionList(False, items)

	def build_fields(self):
		self.fields = []
		for df in self.meta["fields"]:
			if df["fieldtype"] in ["Section Break", "Column Break"]:
				continue
			self.fields.append(df)

		standard_fields = (
			{
				"fieldname": "name",
				"label": "name",
				"fieldtype": "Data",
				"description": "The primary key of the document",
			},
			{
				"fieldname": "owner",
				"label": "owner",
				"fieldtype": "Data",
				"description": "Owner of the document",
			},
			{
				"fieldname": "creation",
				"label": "creation",
				"fieldtype": "Datetime",
				"description": "Timestamp at which document was created",
			},
			{
				"fieldname": "modified",
				"label": "modified",
				"fieldtype": "Datetime",
				"description": "Timestamp at which document was modified",
			},
			{
				"fieldname": "modified_by",
				"label": "modified_by",
				"fieldtype": "Data",
				"description": "The last user who modified the document",
			},
			{
				"fieldname": "docstatus",
				"label": "docstatus",
				"fieldtype": "Int",
				"description": "Document Status",
			},
		)
		self.fields.extend(standard_fields)

	def build_jedi_completions(self, force=False):
		if hasattr(self, "jedi_completions") and not force:
			return self.jedi_completions

		print(f"{self.doctype}: building jedi completions")
		apps_path = os.path.join(self.frappe_bench_path, "apps")
		relative_path = os.path.relpath(self.folder, apps_path)
		basename = os.path.basename(relative_path)
		module_path = relative_path.split("/", 1)[1]
		module_path = module_path + "/" + basename
		module_path = module_path.replace("/", ".")
		self.module_name = module_path
		doctype_class = self.doctype.replace(" ", "")
		code = f"""\
from {module_path} import {doctype_class}

doc = {doctype_class}('name')
doc.
"""

		script = jedi.Script(
			code, path="file.py", environment=self.config.get_jedi_environment()
		)
		completions = script.complete(4, 4)
		self.jedi_completions = [c for c in completions if not c.name.startswith("__")]

	def get_docfield_details(self, df, join_by="\n"):
		field_meta = [df.get("label") or ""]
		fieldtype = df["fieldtype"]
		field_meta.append(f"Fieldtype: {fieldtype}")

		options = df.get("options")
		if fieldtype == "Select" and options:
			select_options = ", ".join(options.split("\n"))
			field_meta.append(f"Options: {select_options}")
		elif options:
			field_meta.append(f"Options: {options}")

		description = df.get("description")
		field_meta = "\n\n".join(field_meta)
		return f'{description or ""}\n\n{field_meta}'


def lsp_completion_item(name: Completion, module_name: str) -> CompletionItem:
	"""Using a Jedi completion, obtain a jedi completion item."""
	name_name = name.name
	# name_clean = clean_completion_name(name_name, char_before_cursor)
	jedi_completion_type_map = {
		"module": CompletionItemKind.Module,
		"class": CompletionItemKind.Class,
		"instance": CompletionItemKind.Variable,
		"function": CompletionItemKind.Function,
		"param": CompletionItemKind.Variable,
		"path": CompletionItemKind.File,
		"keyword": CompletionItemKind.Keyword,
		"statement": CompletionItemKind.Variable,
	}
	lsp_type = jedi_completion_type_map[name.type]

	sort_text = "y"
	if name.module_name == module_name:
		sort_text = "x"
	if name.type == "param" and name.name.endswith("="):
		sort_text = "a"
	if name.name.startswith("_"):
		sort_text = "z"

	completion_item = CompletionItem(
		label=name_name,
		filter_text=name_name,
		kind=lsp_type,
		detail=name.description,
		documentation=MarkupContent(kind="markdown", value=name.docstring()),
		sort_text=sort_text,
		insert_text=name_name,
		insert_text_format=InsertTextFormat.PlainText,
	)

	return completion_item
	# if not enable_snippets:
	# 	return completion_item
	# if lsp_type not in _LSP_TYPE_FOR_SNIPPET:
	# 	return completion_item

	# signatures = name.get_signatures()
	# if not signatures:
	# 	return completion_item

	# try:
	# 	snippet_signature = get_snippet_signature(signatures[0])
	# except Exception:  # pylint: disable=broad-except
	# 	return completion_item
	# new_text = name_name + snippet_signature
	# completion_item.insertText = new_text
	# completion_item.insertTextFormat = InsertTextFormat.Snippet
	# return completion_item
