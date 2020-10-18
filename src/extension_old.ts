// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { setupDiagnostics } from "./diagnostics";
import { debugMsg, getDocTypeJSON, findFrappeBenchDir } from "./utils";
import { setupAutocomplete } from "./autocomplete";
import { setupHover } from "./hover";
import { setupDefinition } from "./definition";

export async function activate(context: vscode.ExtensionContext) {
  if (!findFrappeBenchDir()) {
    debugMsg("Frappe Bench Directory not found");
    return;
  }

  if (vscode.window.activeTextEditor) {
    // try and get doctype json for active editor
    getDocTypeJSON(vscode.window.activeTextEditor.document);
  }

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) {
        // try and get doctype json when active editor changes
        getDocTypeJSON(editor.document);
      }
    })
  );

  setupDiagnostics(context);
  setupAutocomplete(context);
  setupHover(context);
  setupDefinition(context);
}

// this method is called when your extension is deactivated
export function deactivate() {}
