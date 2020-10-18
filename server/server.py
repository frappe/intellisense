import asyncio
import time
import uuid


from pygls.features import (
	COMPLETION,
	EXIT,
	INITIALIZED,
	TEXT_DOCUMENT_DID_CHANGE,
	TEXT_DOCUMENT_DID_CLOSE,
	TEXT_DOCUMENT_DID_OPEN,
	TEXT_DOCUMENT_DID_SAVE,
	INITIALIZE,
	WORKSPACE_FOLDERS,
)
from pygls.server import LanguageServer
from pygls.types import (
	CompletionItem,
	CompletionList,
	CompletionParams,
	ConfigurationItem,
	ConfigurationParams,
	Diagnostic,
	DidChangeTextDocumentParams,
	DidCloseTextDocumentParams,
	DidOpenTextDocumentParams,
	DidSaveTextDocumentParams,
	MessageType,
	Position,
	Range,
	Registration,
	RegistrationParams,
	Unregistration,
	UnregistrationParams,
	WorkspaceSymbolParams,
)
from .diagnostics import get_translation_diagnostics
from .autocomplete import get_document_autocompletion_items
from .utils import find_frappe_bench_dir

COUNT_DOWN_START_IN_SECONDS = 10
COUNT_DOWN_SLEEP_IN_SECONDS = 1


class FrappeLanguageServer(LanguageServer):
	CMD_COUNT_DOWN_BLOCKING = "countDownBlocking"
	CMD_COUNT_DOWN_NON_BLOCKING = "countDownNonBlocking"
	CMD_REGISTER_COMPLETIONS = "registerCompletions"
	CMD_SHOW_CONFIGURATION_ASYNC = "showConfigurationAsync"
	CMD_SHOW_CONFIGURATION_CALLBACK = "showConfigurationCallback"
	CMD_SHOW_CONFIGURATION_THREAD = "showConfigurationThread"
	CMD_UNREGISTER_COMPLETIONS = "unregisterCompletions"

	CONFIGURATION_SECTION = "frappe-intellisense"

	def __init__(self):
		super().__init__()


server = FrappeLanguageServer()


# @server.feature(INITIALIZE)
# def initialize(ls: FrappeLanguageServer):
# 	frappe_bench_dir = find_frappe_bench_dir(ls)

# @server.feature(WORKSPACE_FOLDERS)
# def workspace_folders(ls: FrappeLanguageServer, params):
# 	ls.show_message("workspace")


@server.feature(COMPLETION, trigger_characters=["."])
def completions(ls: FrappeLanguageServer, params: CompletionParams = None):
	"""Returns completion items."""
	return get_document_autocompletion_items(ls, params)


@server.command(FrappeLanguageServer.CMD_COUNT_DOWN_BLOCKING)
def count_down_10_seconds_blocking(ls, *args):
	"""Starts counting down and showing message synchronously.
	It will `block` the main thread, which can be tested by trying to show
	completion items.
	"""
	for i in range(COUNT_DOWN_START_IN_SECONDS):
		ls.show_message("Counting down... {}".format(COUNT_DOWN_START_IN_SECONDS - i))
		time.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@server.command(FrappeLanguageServer.CMD_COUNT_DOWN_NON_BLOCKING)
async def count_down_10_seconds_non_blocking(ls, *args):
	"""Starts counting down and showing message asynchronously.
	It won't `block` the main thread, which can be tested by trying to show
	completion items.
	"""
	for i in range(COUNT_DOWN_START_IN_SECONDS):
		ls.show_message("Counting down... {}".format(COUNT_DOWN_START_IN_SECONDS - i))
		await asyncio.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


# @server.feature(TEXT_DOCUMENT_DID_CHANGE)
# def did_change(ls, params: DidChangeTextDocumentParams):
# 	"""Text document did change notification."""
# 	send_diagnostics(ls, params)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: DidSaveTextDocumentParams):
	"""Text document did save notification."""
	send_diagnostics(ls, params)


@server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: FrappeLanguageServer, params: DidCloseTextDocumentParams):
	"""Text document did close notification."""
	server.show_message("Text Document Did Close")


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
	"""Text document did open notification."""
	ls.show_message("Text Document Did Open")
	send_diagnostics(ls, params)


@server.command(FrappeLanguageServer.CMD_REGISTER_COMPLETIONS)
async def register_completions(ls: FrappeLanguageServer, *args):
	"""Register completions method on the client."""
	params = RegistrationParams(
		[Registration(str(uuid.uuid4()), COMPLETION, {"triggerCharacters": "[':']"})]
	)
	response = await ls.register_capability_async(params)
	if response is None:
		ls.show_message("Successfully registered completions method")
	else:
		ls.show_message("Error happened during completions registration.", MessageType.Error)


@server.command(FrappeLanguageServer.CMD_SHOW_CONFIGURATION_ASYNC)
async def show_configuration_async(ls: FrappeLanguageServer, *args):
	"""Gets exampleConfiguration from the client settings using coroutines."""
	try:
		config = await ls.get_configuration_async(
			ConfigurationParams(
				[ConfigurationItem("", FrappeLanguageServer.CONFIGURATION_SECTION)]
			)
		)

		example_config = config[0].exampleConfiguration

		ls.show_message("jsonServer.exampleConfiguration value: {}".format(example_config))

	except Exception as e:
		ls.show_message_log("Error ocurred: {}".format(e))


@server.command(FrappeLanguageServer.CMD_SHOW_CONFIGURATION_CALLBACK)
def show_configuration_callback(ls: FrappeLanguageServer, *args):
	"""Gets exampleConfiguration from the client settings using callback."""

	def _config_callback(config):
		try:
			example_config = config[0].exampleConfiguration

			ls.show_message("jsonServer.exampleConfiguration value: {}".format(example_config))

		except Exception as e:
			ls.show_message_log("Error ocurred: {}".format(e))

	ls.get_configuration(
		ConfigurationParams(
			[ConfigurationItem("", FrappeLanguageServer.CONFIGURATION_SECTION)]
		),
		_config_callback,
	)


@server.thread()
@server.command(FrappeLanguageServer.CMD_SHOW_CONFIGURATION_THREAD)
def show_configuration_thread(ls: FrappeLanguageServer, *args):
	"""Gets exampleConfiguration from the client settings using thread pool."""
	try:
		config = ls.get_configuration(
			ConfigurationParams(
				[ConfigurationItem("", FrappeLanguageServer.CONFIGURATION_SECTION)]
			)
		).result(2)

		example_config = config[0].exampleConfiguration

		ls.show_message("jsonServer.exampleConfiguration value: {}".format(example_config))

	except Exception as e:
		ls.show_message_log("Error ocurred: {}".format(e))


@server.command(FrappeLanguageServer.CMD_UNREGISTER_COMPLETIONS)
async def unregister_completions(ls: FrappeLanguageServer, *args):
	"""Unregister completions method on the client."""
	params = UnregistrationParams([Unregistration(str(uuid.uuid4()), COMPLETION)])
	response = await ls.unregister_capability_async(params)
	if response is None:
		ls.show_message("Successfully unregistered completions method")
	else:
		ls.show_message(
			"Error happened during completions unregistration.", MessageType.Error
		)


def send_diagnostics(ls, params):
	diagnostics = get_translation_diagnostics(ls, params)
	ls.publish_diagnostics(params.textDocument.uri, diagnostics)
