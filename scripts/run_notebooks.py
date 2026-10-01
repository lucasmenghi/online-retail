"""Executa e valida os notebooks em ordem a partir de qualquer diretório."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    for name in ["00_discovery.ipynb", "01_preparation.ipynb", "02_modeling.ipynb", "03_final_model.ipynb"]:
        path = root / name
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        NotebookClient(notebook, timeout=600, resources={"metadata": {"path": str(root)}}).execute()
        # Não publicar caminho pessoal do interpretador nas saídas.
        for cell in notebook.cells:
            for output in cell.get("outputs", []):
                if output.output_type == "stream" and "Interpretador:" in output.get("text", ""):
                    output.text = "\n".join(line for line in output.text.splitlines() if not line.startswith("Interpretador:"))
        nbformat.write(notebook, path)
        print(f"Executado: {name}", flush=True)
