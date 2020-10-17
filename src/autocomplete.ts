import * as vscode from "vscode";
import { getDocTypeJSON } from "./utils";

export function setupAutocomplete(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider(
      "python",
      {
        async provideCompletionItems(
          document: vscode.TextDocument,
          position: vscode.Position
        ): Promise<vscode.CompletionList<vscode.CompletionItem>> {
          let doctypeJSON = getDocTypeJSON(document);
          if (doctypeJSON) {
            let lineText = document.lineAt(position.line).text;
            let lineTillCurrentPosition = lineText.substr(
              0,
              position.character
            );

            if (lineTillCurrentPosition.trim() === "self.") {
              return Promise.resolve(getDocTypeClassItems(doctypeJSON));
            }
          }
          return Promise.resolve(new vscode.CompletionList([], false));
        },
      },
      "."
    )
  );
}

interface DocTypeJSON {
  fields: DocField[];
}

export interface DocField {
  fieldname: string;
  fieldtype: string;
  label: string;
  description: string;
  options: string;
}

function getDocTypeClassItems(doctypeJSON: DocTypeJSON) {
  return new vscode.CompletionList(
    doctypeJSON.fields
      .filter(
        (df: DocField) =>
          !["Section Break", "Column Break"].includes(df.fieldtype)
      )
      .map((df) => {
        let i: vscode.CompletionItem = {
          label: df.fieldname,
          kind: vscode.CompletionItemKind.Field,
          documentation: getDocFieldDetails(df),
          sortText: "a",
        };
        return i;
      }),
    false
  );
}

export function getDocFieldDetails(df: DocField, joinBy = "\n") {
  let fieldMeta = [df.description || df.label];

  fieldMeta.push(`Fieldtype: ${df.fieldtype}`);

  if (df.fieldtype === "Select" && df.options) {
    fieldMeta.push(`Options: ${df.options.split("\n").join(", ")}`);
  } else if (df.options) {
    fieldMeta.push(`Options: ${df.options}`);
  }
  return fieldMeta.join(joinBy);
}
