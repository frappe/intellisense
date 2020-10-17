import * as vscode from "vscode";
export function setupDiagnostics(context: vscode.ExtensionContext) {
  const collection = vscode.languages.createDiagnosticCollection("frappe-lint");
  if (vscode.window.activeTextEditor) {
    // update diagnostics for active editor
    updateDiagnostics(vscode.window.activeTextEditor.document, collection);
  }
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      // update diagnostics when file is saved
      updateDiagnostics(document, collection);
    })
  );
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) {
        // update diagnostics when active editor changes
        updateDiagnostics(editor.document, collection);
      }
    })
  );
}

function updateDiagnostics(
  document: vscode.TextDocument,
  collection: vscode.DiagnosticCollection
): void {
  if (document) {
    let warnings = getTranslationWarnings(document);

    let diagnostics = warnings.map((warning) => {
      return {
        code: "",
        message: warning.message,
        range: warning.range,
        severity: vscode.DiagnosticSeverity.Error,
        source: "",
      };
    });
    collection.set(document.uri, diagnostics);
  } else {
    collection.clear();
  }
}

function getTranslationWarnings(document: vscode.TextDocument) {
  let warnings = [];
  let pattern = /_\(([\"']{0,3})(?<message>((?!\1).)*)\1(s*,s*contexts*=s*([\"'])(?<py_context>((?!\5).)*)\5)*(s*,s*(.)*?s*(,s*([\"'])(?<js_context>((?!\11).)*)\11)*)*\)/;
  let wordsPattern = /_{1,2}\([\"'`]{1,3}.*?[a-zA-Z]/;
  let startPattern = /_{1,2}\([f\"'`]{1,3}/;
  let fStringPattern = /_\(f[\"']/;
  let startsWithFPattern = /_\(f/;

  for (let i = 0; i < document.lineCount; i++) {
    let line = document.lineAt(i);
    if (line.text.includes("frappe-lint: disable-translate")) {
      continue;
    }
    if (!startPattern.test(line.text)) {
      continue;
    }
    let startsWithF = startsWithFPattern.test(line.text);
    if (startsWithF) {
      let hasFString = fStringPattern.test(line.text);
      if (hasFString) {
        warnings.push({
          message: "F-strings are not supported for translations",
          range: new vscode.Range(
            new vscode.Position(i, line.firstNonWhitespaceCharacterIndex),
            line.range.end
          ),
        });
        continue;
      } else {
        continue;
      }
    }

    let match = pattern.test(line.text);
    let errorFound = false;

    if (!match && line.text.endsWith(",\n")) {
      // TODO: handle multiline strings
      // concat remaining text to validate multiline pattern
      // line = "".join(file_lines[line_number - 1:])
      // line = line[start_matches.start() + 1:]
      // match = pattern.match(line)
    }

    if (!match) {
      errorFound = true;
      warnings.push({
        message: "Translation syntax error",
        range: line.range,
      });
    }

    if (!errorFound && !wordsPattern.test(line.text)) {
      warnings.push({
        message: "Translation is useless because it has no words",
        range: line.range,
      });
    }
  }

  return warnings;
}
