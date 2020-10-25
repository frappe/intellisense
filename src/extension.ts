import * as net from "net";
import * as path from "path";
import * as cp from "child_process";
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
  let { done, reason } = await checkDependencies();
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
    const pythonPath = getPythonPath();

    if (!pythonPath) {
      throw new Error("`python.pythonPath` is not set");
    }

    client = startLangServer(pythonPath, ["-m", "server"], cwd);
  }

  context.subscriptions.push(client.start());
}

export function deactivate(): Thenable<void> {
  return client ? client.stop() : Promise.resolve();
}

async function checkDependencies() {
  let exec = promisify(cp.exec);
  let pythonPath = getPythonPath();

  let { stdout: version, stderr: versionErr } = await exec(
    `${pythonPath} --version`
  );
  if (!(version || versionErr).includes("Python 3.")) {
    return {
      done: false,
      reason:
        "Frappe Intellisense works only with Python 3. Update your pythonPath configuration to a Python 3 binary",
    };
  }

  vscode.window.showInformationMessage(
    "[Frappe Language Server] Checking dependencies..."
  );

  try {
    let command = `${pythonPath} -c "import sys; print(sys.path);"`;
    await exec(command);
  } catch (error) {
    return {
      done: false,
      reason:
        "Frappe Intellisense requires pygls to be installed. Install it using 'pip install pygls'",
    };
  }

  return {
    done: true,
  };
}

function getPythonPath() {
  return workspace.getConfiguration("python").get<string>("pythonPath");
}
