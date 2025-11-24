# NL2FOL: Translating Natural Language to First Order Logic for Logical Fallacy Detection

This project implements a neuro-symbolic pipeline designed to detect logical fallacies by translating natural language arguments into First Order Logic (FOL). By leveraging the semantic understanding of Large Language Models (LLMs) and the rigorous reasoning capabilities of SMT solvers (Satisfiability Modulo Theories), NL2FOL provides a robust framework for formal argument verification.

## Key Features

*   **Neuro-Symbolic Approach**: Combines LLMs (GPT-4, Gemini, Llama) with symbolic reasoning (CVC4/CVC5).
*   **Automated Translation**: Converts complex natural language sentences into structured First Order Logic formulas.
*   **Logical Fallacy Detection**: Identifies invalid arguments by checking satisfiability.
*   **Entity & Relation Mapping**: Uses Natural Language Inference (NLI) to resolve entity relationships (subsets, equality) within arguments.
*   **Explainable Results**: Provides counter-examples for detected fallacies.

## Project Structure

*   `src/`: Core source code for the pipeline.
    *   `nl_to_fol.py`: Main script for decomposing text and generating FOL.
    *   `fol_to_cvc.py`: Interface for running the SMT solver on generated FOL.
    *   `cvc.py`: Helper class for generating CVC SMT-LIB scripts.
    *   `interpret_smt_results.py`: Tool to interpret solver outputs and generate explanations.
*   `eval/`: Evaluation scripts.
    *   `get_metrics.py`: Computes accuracy, precision, recall, and F1 scores.
*   `prompts/`: Collection of prompt templates used for LLM querying.
*   `data/`: Datasets used for training and testing (Logic, LogicClimate, NLI, Folio).

## Installation

1.  **Clone the repository**
2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install SMT Solver**:
    *   Download and install [CVC5](https://cvc5.github.io/) or [CVC4](https://cvc4.github.io/).
    *   Ensure the binary is accessible in your system PATH or set the `CVC_BIN` environment variable to the executable path.

## Usage Instructions

### 1. Convert Natural Language to First Order Logic
This step processes the dataset, interacts with the LLM, and generates FOL representations for claims and implications.

```bash
python src/nl_to_fol.py --model_name <your_model_name> --nli_model_name <your_nli_model_name>  --run_name <run_name> --dataset <dataset_name> --length <num_samples>
```

**Arguments:**
*   `--model_name`: The LLM to use (e.g., `gpt-4o`, `gemini`, or a HuggingFace model path like `meta-llama/Llama-2-7b-hf`).
*   `--nli_model_name`: Model used for Natural Language Inference (e.g., `cross-encoder/nli-deberta-v3-base`).
*   `--run_name`: Identifier for the output file (saved in `results/`).
*   `--dataset`: Dataset to use (`logic`, `logicclimate`, `folio`, or `nli`).
*   `--length`: Number of datapoints to sample.

### 2. Verify Logic with SMT Solver
Converts the generated FOL into SMT-LIB format and runs the CVC solver to check for validity.

```bash
python src/fol_to_cvc.py <run_name>
```
*Note: The `<run_name>` should match the one used in step 1.*

### 3. Evaluate Performance
Calculate metrics (Accuracy, F1, Precision, Recall) based on the solver's results.

```bash
python eval/get_metrics.py results/<run_name>_results.csv
```

### 4. Interpret SMT Results
Generate a human-readable explanation or counter-example for a specific result.

```bash
python src/interpret_smt_results.py <output_of_smt_file_path> <json_data_path>
```
*   `<output_of_smt_file_path>`: Path to the `.txt` output from the solver (in `results/<run_name>_smt/`).
*   `<json_data_path>`: Path to the JSON file containing sentence data (optional/specific use case).

## Methodology

The pipeline follows these stages:
1.  **Decomposition**: The input argument is split into a **Claim** (Premise) and an **Implication** (Conclusion).
2.  **Entity Extraction**: Referring expressions and properties are identified.
3.  **Relation Modeling**: NLI models determine relationships between entities (e.g., "All cats are mammals" -> Cats $\subseteq$ Mammals).
4.  **FOL Construction**: Components are assembled into a logical formula: $(Claim \wedge Relations) \rightarrow Implication$.
5.  **SMT Solving**: The formula is negated and passed to the SMT solver. If `Unsat`, the argument is **Valid**. If `Sat`, it is a **Fallacy**.

## Environment Configuration

To run the pipeline, you must set up the following environment variables for API access:

*   `HUGGINGFACE_HUB_TOKEN`: Required for accessing Llama and other models from Hugging Face.
*   `GEMINI_API_KEY`: Required if using Google's Gemini models.

You can set these in your terminal or use a `.env` file:

```bash
export HUGGINGFACE_HUB_TOKEN="your_token_here"
export GEMINI_API_KEY="your_key_here"
```

## Datasets

The project supports several datasets for evaluation:

*   **`logic`**: General logical fallacy dataset (`data/fallacies.csv`).
*   **`logicclimate`**: Climate change-related fallacies (`data/fallacies_climate.csv`).
*   **`nli`**: Natural Language Inference based fallacies (`data/nli_fallacies_test.csv`).

## Example Workflow

Here is a complete example of running the pipeline on the `logic` dataset using Gemini 2.5:

1.  **Generate Logic**:
    ```bash
    python src/nl_to_fol.py --model_name gemini-2.5-flash --nli_model_name roberta-large-mnli --run_name test_run01 --length 50 --dataset logic
    ```

2.  **Verify Validity**:
    ```bash
    python src/fol_to_cvc.py test_run_01
    ```

3.  **Get Metrics**:
    ```bash
    python eval/get_metrics.py results/test_run_01_results.csv
    ```