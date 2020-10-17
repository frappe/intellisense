import * as vscode from "vscode";
import { getDocTypeJSON } from "./utils";
import { getDocFieldDetails } from "./autocomplete";

export function setupHover(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.languages.registerHoverProvider("python", {
      provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
      ) {
        let wordRange = document.getWordRangeAtPosition(position);
        if (wordRange) {
          let word = document.getText(
            new vscode.Range(
              new vscode.Position(position.line, wordRange.start.character - 5),
              wordRange.end
            )
          );

          if (word.startsWith("self.")) {
            let doctypeJSON = getDocTypeJSON(document);
            for (let df of doctypeJSON.fields) {
              let selfFieldname = "self." + df.fieldname;
              if (word === selfFieldname) {
                return new vscode.Hover(
                  getDocFieldDetails(df, ", "),
                  wordRange
                );
              }
            }
          }
        }
        return new vscode.Hover("test est");
      },
    })
  );
}
