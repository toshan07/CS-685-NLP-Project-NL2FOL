import pandas as pd
import sys
import subprocess
import shutil
import os
from cvc import CVCGenerator

def find_cvc_binary():
    env_bin = os.environ.get("CVC_BIN")
    candidates = []
    if env_bin:
        candidates.append(env_bin)
    base_names = ["cvc5", "cvc5.exe", "cvc4", "cvc4.exe", "./cvc5", "./cvc4"]
    candidates.extend(base_names)

    for name in candidates:
        path = shutil.which(name)
        if path:
            return path
        if os.path.isfile(name) and os.access(name, os.X_OK):
            return os.path.abspath(name)
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fol_to_cvc.py <run name>")
        sys.exit(1)
    run_name = sys.argv[1]
    csv_file = f"results/{run_name}.csv"
    if not os.path.isfile(csv_file):
        print(f"CSV file not found: {csv_file}")
        sys.exit(1)

    cvc_bin = find_cvc_binary()
    if cvc_bin is None:
        print("ERROR: Could not find a CVC binary (cvc5 or cvc4).")
        print("Install cvc5 for Windows (download cvc5-x86_64-windows-msvc.zip) or set environment var CVC_BIN to its path.")
        sys.exit(1)
    else:
        print(f"Using CVC binary: {cvc_bin}")

    out_dir = f"results/{run_name}_smt"
    os.makedirs(out_dir, exist_ok=True)

    data = pd.read_csv(csv_file)
    fol_col = None
    for candidate in ['Logical Form 2', 'Logical Form', 'final_lf', 'final_lf2']:
        if candidate in data.columns:
            fol_col = candidate
            break
    if fol_col is None:
        print("ERROR: No recognized logical form column found in CSV.")
        print("Columns available:", list(data.columns))
        sys.exit(1)

    fol = data[fol_col]
    results = []
    for i in range(len(fol)):
        lf = fol[i]
        print(i, lf)
        try:
            if not isinstance(lf, str) or lf.strip() == "":
                print(f"Row {i}: empty or non-string logical form.")
                results.append("")
                continue

            sanitized = lf.replace("ForAll", "forall").replace("ThereExists", "exists").replace("&", "and").replace("~", "not ")
            script = CVCGenerator(sanitized).generateCVCScript()
            smt_path = os.path.join(out_dir, f"{i}.smt2")
            out_txt_path = os.path.join(out_dir, f"{i}_out.txt")

            with open(smt_path, "w", encoding="utf-8") as f:
                f.write(script)

            proc = subprocess.run([cvc_bin, smt_path], capture_output=True, text=True, check=False)
            proc_stdout = proc.stdout or ""
            proc_stderr = proc.stderr or ""
            combined = proc_stdout + ("\n---stderr---\n" + proc_stderr if proc_stderr else "")

            with open(out_txt_path, "w", encoding="utf-8") as f:
                f.write(combined)

            first_line = ""
            if proc_stdout.strip() != "":
                first_line = proc_stdout.splitlines()[0].strip().lower()
            elif proc_stderr.strip() != "":
                first_line = proc_stderr.splitlines()[0].strip().lower()
            else:
                first_line = ""

            if "unsat" in first_line:
                results.append("Valid")
            elif "unknown" in first_line or "sat" in first_line:
                results.append("LF")
            else:
                print(f"Row {i}: solver returned no clear result ('{first_line}'). Trying finite-model-finding mode...")
                try:
                    script2 = CVCGenerator(sanitized).generateCVCScript(finite_model_finding=True)
                    with open(smt_path, "w", encoding="utf-8") as f2:
                        f2.write(script2)
                    proc2 = subprocess.run([cvc_bin, smt_path], capture_output=True, text=True, check=False)
                    proc2_stdout = proc2.stdout or ""
                    proc2_stderr = proc2.stderr or ""
                    with open(out_txt_path, "a", encoding="utf-8") as f2:
                        f2.write("\n=== second run (finite model finding) ===\n")
                        f2.write(proc2_stdout)
                        if proc2_stderr:
                            f2.write("\n---stderr---\n")
                            f2.write(proc2_stderr)

                    first_line2 = ""
                    if proc2_stdout.strip() != "":
                        first_line2 = proc2_stdout.splitlines()[0].strip().lower()
                    elif proc2_stderr.strip() != "":
                        first_line2 = proc2_stderr.splitlines()[0].strip().lower()

                    if "unsat" in first_line2:
                        results.append("Valid")
                    elif "unknown" in first_line2 or "sat" in first_line2:
                        results.append("LF")
                    else:
                        results.append("")
                except Exception as e:
                    print(f"Row {i}: error during second attempt: {e}")
                    results.append("")
        except Exception as e:
            print(f"Cannot run this statement : {e}")
            results.append("")
            continue

    data['result'] = results
    out_csv = f"results/{run_name}_results.csv"
    data.to_csv(out_csv, index=False)
    print(f"Wrote results to {out_csv}")