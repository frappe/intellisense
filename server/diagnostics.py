import re

from pygls.lsp.types import Diagnostic, Position, Range


def get_translation_diagnostics(ls, params):
	document = ls.workspace.get_document(params.text_document.uri)

	pattern = re.compile(
		r"_\(([\"']{,3})(?P<message>((?!\1).)*)\1(\s*,\s*context\s*=\s*([\"'])(?P<py_context>((?!\5).)*)\5)*(\s*,\s*(.)*?\s*(,\s*([\"'])(?P<js_context>((?!\11).)*)\11)*)*\)"
	)
	words_pattern = re.compile(r"_{1,2}\([\"'`]{1,3}.*?[a-zA-Z]")
	start_pattern = re.compile(r"_{1,2}\([f\"'`]{1,3}")
	f_string_pattern = re.compile(r"_\(f[\"']")
	starts_with_f_pattern = re.compile(r"_\(f")

	diagnostics = []
	source = type(ls).__name__

	for line_number, line in enumerate(document.lines):
		if "frappe-lint: disable-translate" in line:
			continue

		last_character_index = len(line) - 1
		first_non_white_space_character_index = len(line) - len(line.lstrip())

		start_matches = start_pattern.search(line)
		if start_matches:
			starts_with_f = starts_with_f_pattern.search(line)

			if starts_with_f:
				has_f_string = f_string_pattern.search(line)
				if has_f_string:
					d = Diagnostic(
						range=Range(
							Position(line=line_number, character=first_non_white_space_character_index),
							Position(line=line_number, character=last_character_index),
						),
						message="F-strings are not supported for translations",
						source=source,
					)
					diagnostics.append(d)
					continue
				else:
					continue

			match = pattern.search(line)
			error_found = False

			if not match and line.endswith(",\n"):
				# concat remaining text to validate multiline pattern
				line = "".join(document.lines[line_number - 1 :])
				line = line[start_matches.start() + 1 :]
				match = pattern.match(line)

			if not match:
				error_found = True
				d = Diagnostic(
					range=Range(
						Position(line=line_number, character=first_non_white_space_character_index),
						Position(line=line_number, character=last_character_index),
					),
					message="Translation syntax error",
					source=source,
				)
				diagnostics.append(d)

			if not error_found and not words_pattern.search(line):
				error_found = True
				d = Diagnostic(
					range=Range(
						start=Position(line=line_number, character=first_non_white_space_character_index),
						end=Position(line=line_number, character=last_character_index),
					),
					message="Translation is useless because it has no words",
					source=source,
				)
				diagnostics.append(d)

	return diagnostics
