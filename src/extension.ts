import * as net from "net";
import * as path from "path";
import * as cp from "child_process";
import * as fs from "fs";
import * as vscode from "vscode";
import { promisify } from "util";
import { ExtensionContext, workspace } from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from "vscode-languageclient";

let client: LanguageClient;

function getClientOptions(): LanguageClientOptions {
  return {
    // Register the server for plain text documents
    documentSelector: ["python", "plaintext"],
    outputChannelName: "Frappe Language Server",
    synchronize: {
      // Notify the server about file changes to '.clientrc files contain in the workspace
      fileEvents: workspace.createFileSystemWatcher("**/.clientrc"),
    },
  };
}

function isStartedInDebugMode(): boolean {
  return process.env.VSCODE_DEBUG_MODE === "true";
}

function startLangServerTCP(addr: number): LanguageClient {
  const serverOptions: ServerOptions = () => {
    return new Promise((resolve, reject) => {
      const clientSocket = new net.Socket();
      clientSocket.connect(addr, "127.0.0.1", () => {
        resolve({
          reader: clientSocket,
          writer: clientSocket,
        });
      });
    });
  };

  return new LanguageClient(
    `tcp lang server (port ${addr})`,
    serverOptions,
    getClientOptions()
  );
}

function startLangServer(
  command: string,
  args: string[],
  cwd: string
): LanguageClient {
  const serverOptions: ServerOptions = {
    args,
    command,
    options: { cwd },
  };

  return new LanguageClient(command, serverOptions, getClientOptions());
}

export async function activate(context: ExtensionContext) {
  let frappeBenchDir = findFrappeBench();

  if (!frappeBenchDir) {
    return;
  }

  let { done, reason } = await checkDependencies(frappeBenchDir);
  if (!done) {
    if (reason) {
      vscode.window.showInformationMessage(reason);
    }
    return;
  }

  if (isStartedInDebugMode()) {
    // Development - Run the server manually
    client = startLangServerTCP(2087);
  } else {
    // Production - Client is going to run the server (for use within `.vsix` package)
    const cwd = path.join(__dirname, "..");
    const pythonPath = path.resolve(frappeBenchDir, "env", "bin", "python");

    client = startLangServer(pythonPath, ["-m", "server"], cwd);
  }

  context.subscriptions.push(client.start());
}

export function deactivate(): Thenable<void> {
  return client ? client.stop() : Promise.resolve();
}

async function checkDependencies(frappeBenchDir: string) {
  let exec = promisify(cp.exec);
  let pythonPath = path.resolve(frappeBenchDir, "env", "bin", "python");

  let { stdout: version, stderr: versionErr } = await exec(
    `${pythonPath} --version`
  );
  if (!(version || versionErr).includes("Python 3.")) {
    return {
      done: false,
      reason:
        "Frappe Intellisense works only with Python 3. Update your python version to version 3.",
    };
  }

  try {
    let command = `${pythonPath} -c "import jedi, pygls"`;
    await exec(command);
  } catch (error) {
    let value = await vscode.window.showInformationMessage(
      "[Frappe Language Server] Dependencies not found. Install missing dependencies pygls and jedi ?",
      "Yes",
      "No"
    );
    if (value === "Yes") {
      try {
        await vscode.window.withProgress(
          {
            location: vscode.ProgressLocation.Notification,
            title: "Installing dependencies...",
          },
          async () => {
            try {
              await exec("bench pip install jedi pygls", {
                cwd: frappeBenchDir,
              });
              vscode.window.showInformationMessage(
                "[Frappe Language Server] pygls and jedi installed."
              );
            } catch (error) {
              vscode.window.showInformationMessage(
                "[Frappe Language Server] Could not install dependencies. Install it manually using 'bench pip install pygls jedi'"
              );
              throw new Error("Could not install dependencies");
            }
          }
        );
      } catch (error) {
        return {
          done: false,
          reason: "[Frappe Language Server] Something went wrong.",
        };
      }
    } else {
      return {
        done: false,
      };
    }
  }

  return {
    done: true,
  };
}

function findFrappeBench(): string {
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
