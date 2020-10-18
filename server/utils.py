import os

frappe_bench_dir = None


def find_frappe_bench_dir(ls=None):
	global frappe_bench_dir

	if not frappe_bench_dir and ls:
		current_dir = ls.workspace.root_path
		while True:
			dirs = [d for d in os.listdir(current_dir)]
			if set(["apps", "sites", "Procfile"]).issubset(set(dirs)):
				frappe_bench_dir = current_dir
				ls.show_message(f"Frappe Bench Directory found at {frappe_bench_dir}")
				break
			else:
				current_dir = os.path.abspath(os.path.join(current_dir, ".."))

	return frappe_bench_dir
