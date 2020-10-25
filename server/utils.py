import os


def guess_doctype(document):
	from .server import get_config

	py_path = document.path
	if not py_path.endswith(".py"):
		return

	config = get_config()
	doctypes = config.get("doctypes")
	doctype_paths = doctypes.values()
	document_folder = os.path.abspath(os.path.join(py_path, ".."))

	if document_folder in doctype_paths:
		folder_name = os.path.basename(document_folder)
		py_name = os.path.basename(py_path)
		if (folder_name + ".py") == py_name:
			doctype = list(doctypes.keys())[list(doctypes.values()).index(document_folder)]
			return doctype
