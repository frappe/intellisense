import * as vscode from "vscode";
import { executePythonAndGetOutput } from "./utils";

export function setupDefinition(context: vscode.ExtensionContext) {
  if (vscode.window.activeTextEditor) {
    getDocumentInstances(vscode.window.activeTextEditor.document);
  }
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) {
        getDocumentInstances(editor.document);
      }
    })
  );

  context.subscriptions.push(
    vscode.languages.registerDefinitionProvider("python", {
      async provideDefinition(
        document: vscode.TextDocument,
        position: vscode.Position
      ) {
        let documentInstances = await getDocumentInstances(document);
        let wordRange = document.getWordRangeAtPosition(position);

        let line = position.line;
        let start = wordRange?.start.character;

        interface DocumentInstance {
          character: number;
          line: number;
          paths: string[];
        }

        let instance = documentInstances.find(
          (ins: DocumentInstance) =>
            ins.character === start && ins.line - 1 === line
        );

        if (instance) {
          let uri = vscode.Uri.file(instance.paths[0]);
          return new vscode.Location(
            uri,
            new vscode.Range(
              new vscode.Position(0, 0),
              new vscode.Position(0, 5)
            )
          );
        }
      },
    })
  );
}

let documentInstanceMap = new Map();
export async function getDocumentInstances(document: vscode.TextDocument) {
  if (!documentInstanceMap.has(document.uri)) {
    try {
      let output = await executePythonAndGetOutput(
        "document_instances.py",
        document.uri.fsPath
      );
      let documentInstances = JSON.parse(output);
      documentInstanceMap.set(document.uri, documentInstances);
    } catch (e) {
      documentInstanceMap.set(document.uri, null);
    }
  }
  return documentInstanceMap.get(document.uri);
}
