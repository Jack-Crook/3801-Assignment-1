import time
import csv
from sequant import Sequant
from main import read_formulas, tokenize, parse_formula
from Algoritm2 import prove as prove_baseline
from improved_algo2 import prove_improved 
from pathlib import Path

Path("output").mkdir(parents=True, exist_ok=True)

def parse_to_sequant(formula_text):
    tokens = tokenize(formula_text)
    ast = parse_formula(tokens)
    if tokens:
        raise SyntaxError(f"Leftover tokens: {tokens}")
    seq = Sequant([], [ast])
    return seq

def run_prover(formula_text, prover):
    seq = parse_to_sequant(formula_text)
    start = time.perf_counter()
    result = prover(seq)
    elapsed = (time.perf_counter() -start) *1000
    return result, elapsed


def run_improved_prover(formula_text):
    seq = parse_to_sequant(formula_text)
    start = time.perf_counter()
    result, stats = prove_improved(seq)
    elapsed = (time.perf_counter() - start) * 1000
    return result, elapsed

def benchmark_file(input_file='formulas.txt', output_csv='output/benchmark_results.csv'):
    formulas = read_formulas(input_file)
    rows = []
    for f in formulas:
        row = {'formula': f}
        try:
            res_b, ms_b = run_prover(f, prove_baseline)
            row['baseline_result'] = bool(res_b)
            row['baseline_time_ms'] = round(ms_b, 3)

            res_i, ms_i = run_improved_prover(f)
            row['improved_result'] = bool(res_i)
            row['improved_time_ms'] = round(ms_i, 3)

            row['error'] = ''

        except Exception as e:
            row['baseline_result'] = ''
            row['baseline_time_ms'] = ''
            row['improved_result'] = ''
            row['improved_time_ms'] = ''
            row['error'] = str(e)
        rows.append(row)

    with open(output_csv, 'w', newline='') as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                'formula',
                'baseline_result',
                'baseline_time_ms',
                'improved_result',
                'improved_time_ms',
                'error'
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


if __name__ == '__main__':
    benchmark_file()