import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import * as cp from "child_process";
import * as glob from "glob";

let doctypeMetaByDocument = new Map();

export function getDocTypeJSON(document: vscode.TextDocument) {
  let doctypeJSON = doctypeMetaByDocument.get(document.uri);
  if (!doctypeMetaByDocument.has(document.uri)) {
    let fileName = document.fileName;
    try {
      doctypeJSON = require(path.join(
        path.dirname(fileName),
        path.basename(fileName, ".py") + ".json"
      ));
    } catch (error) {
      doctypeJSON = null;
    }
    doctypeMetaByDocument.set(document.uri, doctypeJSON);
  }
  return doctypeJSON;
}

export function executePythonAndGetOutput(
  pythonFile: string,
  ...pythonArgs: string[]
): Promise<string> {
  let stdout = "";
  let stderr = "";
  const extension = vscode.extensions.getExtension(
    "netchampfaris.frappe-intellisense"
  );

  const installPath = extension ? extension.extensionPath : "";

  const pythonInterpreter = path.resolve(
    frappeBenchDir,
    "env",
    "bin",
    "python"
  );

  const args = [path.join(installPath, "out", pythonFile), ...pythonArgs];

  debugMsg(JSON.stringify([pythonInterpreter, args, {}]));

  let p = cp.spawn(pythonInterpreter, args, {});

  p.stdout.on("data", (data: string) => (stdout += data));
  p.stderr.on("data", (data: string) => (stderr += data));
  return new Promise((resolve, reject) => {
    p.on("close", () => {
      debugMsg("stdout: " + stdout);
      debugMsg("stderr: " + stderr);

      resolve(stdout);
    });
    p.on("error", (err: string) => {
      return reject(err);
    });
  });
}

export function debugMsg(msg: string): void {
  const extensionConfig = vscode.workspace.getConfiguration(
    "frappe-intellisense"
  );
  if (extensionConfig.debugMessages) {
    vscode.window.showInformationMessage("[debug] " + msg);
  }
}

let moduleDocTypeMap = new Map();
export function makeModuleDoctypeMap() {
  let startDir = findFrappeBenchDir();

  vscode.window.showInformationMessage("Building doctype map...");
  glob(`${startDir}/apps/**/doctype/*/*.json`, (err, files) => {
    if (err) {
      vscode.window.showInformationMessage("Building doctype map... ERROR");
      return;
    }
    for (let file of files) {
      let json = require(file);
      if (json.doctype === "DocType") {
        let name = path.basename(file, path.extname(file));
        json.filePath = file;
        moduleDocTypeMap.set(name, json);
      }
    }
    vscode.window.showInformationMessage("Building doctype map... DONE");
  });
}

let frappeBenchDir: string;
export function findFrappeBenchDir() {
  if (!frappeBenchDir) {
    frappeBenchDir = getFrappeBenchDir();

    if (frappeBenchDir) {
      debugMsg("Found frappeBenchDir at " + frappeBenchDir);
    }
  }
  return frappeBenchDir;
}

function getFrappeBenchDir() {
  let workspaceFolders = vscode.workspace.workspaceFolders || [];

  if (!workspaceFolders.length) {
    return "";
  }

  for (let workspaceFolder of workspaceFolders) {
    let possibleBenchPath = workspaceFolder.uri.fsPath;

    while (
      !containsItems(fs.readdirSync(possibleBenchPath), [
        "apps",
        "sites",
        "Procfile",
      ])
    ) {
      possibleBenchPath = path.resolve(possibleBenchPath, "..");
    }

    return possibleBenchPath;
  }

  return "";
}

function containsItems(array: string[], items: string[]) {
  return items.every((i: string) => array.includes(i));
}
