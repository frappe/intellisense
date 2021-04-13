import os
import sys
import json
import glob
from jedi.api.environment import Environment
from pygls.lsp.types import DidSaveTextDocumentParams
from .doctype_intellisense import DocTypeIntellisense


class IntellisenseConfig:
	def setup(self, ls):
		if hasattr(self, "_setup_complete"):
			return

		ls.show_message_log("Setting up Frappe Intellisense...")
		self.ls = ls
		self.doctype_meta = {}
		self._doctype_intellisense = {}
		self.jedi_environment = None
		self.frappe_bench_dir = self.find_frappe_bench_dir()
		self._setup_complete = True
		if self.frappe_bench_dir:
			self.config = self.get_or_create()
			self.find_all_doctypes()
			ls.show_message_log("Setup complete.")

	def not_frappe(self):
		return not bool(self.frappe_bench_dir)

	def get(self, key):
		return self.config.get(key)

	def set(self, key, value):
		self.config[key] = value

		json_content = json.dumps(self.config)
		with open(self.config_path, "w") as f:
			f.write(json_content)

		return self.config

	def doctype_intellisense(self, doctype):
		if not self._doctype_intellisense.get(doctype):
			meta = self.read_doctype_meta(doctype)
			folder = self.get("doctypes").get(doctype)
			self._doctype_intellisense[doctype] = DocTypeIntellisense(
				doctype, meta, folder, self
			)
		return self._doctype_intellisense.get(doctype)

	def update_doctype_intellisense(self, params: DidSaveTextDocumentParams):
		from .utils import guess_doctype

		document = self.ls.workspace.get_document(params.text_document.uri)
		doctype = guess_doctype(document)
		if doctype:
			self.doctype_intellisense(doctype).build_jedi_completions(force=True)

	def read_doctype_meta(self, doctype):
		folder = self.get("doctypes")[doctype]
		name = os.path.basename(folder)
		json_content = read_file(os.path.join(folder, name + ".json"))
		return json.loads(json_content)

	def find_frappe_bench_dir(self):
		from os.path import expanduser

		frappe_bench_dir = None
		current_dir = self.ls.workspace.root_path
		home_dir = expanduser("~")

		while current_dir != home_dir:
			dirs = [d for d in os.listdir(current_dir)]
			if set(["apps", "sites", "Procfile"]).issubset(set(dirs)):
				frappe_bench_dir = current_dir
				self.ls.show_message_log(f"Found frappe_bench at {frappe_bench_dir}")
				break
			else:
				current_dir = os.path.abspath(os.path.join(current_dir, ".."))

		if frappe_bench_dir:
			return frappe_bench_dir
		else:
			self.ls.show_message_log(f"This does not look like a Frappe project, skipping.")

	def find_all_doctypes(self):
		if self.config.get("doctypes"):
			return

		paths = glob.glob(
			os.path.join(self.frappe_bench_dir, "apps", "**", "doctype", "*", "*.json"),
			recursive=True,
		)
		doctype_map = {}
		for dt_json_path in paths:
			try:
				doctype_json = read_file(dt_json_path)
				doctype_json = json.loads(doctype_json)
				if isinstance(doctype_json, dict) and doctype_json.get("doctype") == "DocType":
					doctype_path = os.path.abspath(os.path.join(dt_json_path, ".."))
					doctype_map[doctype_json["name"]] = doctype_path
			except Exception:
				print(f"failed for {dt_json_path}")

		self.set("doctypes", doctype_map)

	def get_or_create(self):
		self.config_path = self.get_config_path()
		if not self.config_path:
			self.config_path = os.path.join(self.frappe_bench_dir, "frappe-intellisense.json")
			with open(self.config_path, "w") as f:
				f.write("{}")
				return {}

		content = read_file(self.config_path)

		return json.loads(content)

	def get_config_path(self):
		config_path = os.path.join(self.frappe_bench_dir, "frappe-intellisense.json")
		if os.path.exists(config_path):
			return config_path
		return

	def get_jedi_environment(self):
		if not self.jedi_environment:
			self.jedi_environment = Environment(
				os.path.join(self.frappe_bench_dir, "env", "bin", "python")
			)
		return self.jedi_environment


def read_file(path):
	with open(path, "r") as f:
		return f.read()
