import sys
import os
from os import path


def find_document_instances(filename=None, content=None):
	import ast
	import io
	import json
	import glob
	import frappe
	from frappe import scrub

	if not filename:
		filename = (
			"/Users/farisansari/Projects/benches/frappe-bench/apps/frappe/frappe/core/utils.py"
		)

	def find_assign(line):
		assignments = []
		for d in line.body:
			if isinstance(d, ast.Assign):
				if (
					isinstance(d.value, ast.Call)
					and hasattr(d.value.func, "attr")
					and d.value.func.attr == "get_doc"
				):
					assignments.append(d)
			elif hasattr(d, "body"):
				assignments += find_assign(d)
		return assignments

	if not content:
		with io.open(filename, "r") as f:
			content = f.read()

	parsed = ast.parse(content)
	assignments = find_assign(parsed)
	document_instances = []
	for assignment in assignments:
		args = assignment.value.args
		if len(args) == 2:
			if isinstance(args[0], ast.Str):
				arg = args[0]
				target = assignment.targets[0]
				doctype = arg.s
				scrubbed = scrub(doctype)
				paths = glob.glob(
					path.abspath(
						path.join(frappe.__file__, f"../../../**/doctype/{scrubbed}/{scrubbed}.py")
					),
					recursive=1,
				)
				document_instances.append(
					{
						"doctype": doctype,
						"line": target.lineno,
						"character": target.col_offset,
						"scrub": scrubbed,
						"paths": paths
					}
				)

	print(json.dumps(document_instances))


if len(sys.argv) == 2:
	this, filename = sys.argv
	find_document_instances(filename)
elif len(sys.argv) == 3:
	this, filename, content = sys.argv
	find_document_instances(filename, content)
else:
	find_document_instances()
