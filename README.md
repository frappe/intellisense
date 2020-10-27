# Frappe Framework Intellisense

This project contains a Language Server and a VSCode Client to enable
intellisense in Frappe projects.

## Installation

1. Make sure your `frappe-bench` directory is on Python 3.

   ```sh
   cd frappe-bench
   ./env/bin/python --version
   Python 3.7.7
   ```

2. Install this extension from
   [Marketplace](https://marketplace.visualstudio.com/items?itemName=netchampfaris.frappe-intellisense).
   The extension will download the required dependencies automatically.


## Features

Right now, we have only a few features but this is the starting point of many
more features to come.

### Document autocompletion

In DocType classes, fieldnames will be autocompleted after you type `self.`. For
document objects created by `get_doc` will have fieldnames and method
autocompletions.

![Document Intellisense](https://user-images.githubusercontent.com/9355208/97115700-155ff500-171e-11eb-85f9-6887e4b921fd.gif)

### Translation string diagnostics

Incorrect usage of translation strings will be highlighted in red and reported
as error.

![Translation Diagnostics](https://user-images.githubusercontent.com/9355208/97115697-142ec800-171e-11eb-8e6b-e6fb6f535b97.gif)

### Jump to method source in `patches.txt`

If you command click any patch method in `patches.txt` you will be navigated to
the patch source file.

![Patches Jump to Definition](https://user-images.githubusercontent.com/9355208/97115692-0e38e700-171e-11eb-9f7f-3f783a6883b7.gif)

---

License MIT
