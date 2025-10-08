import sys
from pathlib import Path
import unicodedata
import matplotlib.pyplot as plt

RULES: dict[str, list[tuple[str, float]]] = {
    "Produto Novo": [
        ("Preço Competitivo", 0.95),
        ("Preço Muito Competitivo", 0.87),
        ("Preço Extremamente Competitivo", 0.75),
        ("Preço com Pressa Moderada", 0.62),
        ("Preço com Muita Pressa", 0.49),
        ("Preço com Pressa Extrema e Desespero Moderado", 0.40),
        ("Preço com Pressa Extrema e Extremo Desespero", 0.3333),
    ],
    "Produto Usado": [
        ("Preço Muito Competitivo", 0.95),
        ("Preço Extremamente competitivo", 0.85),
        ("Preço com Moderada Pressa", 0.75),
        ("Preço com Muita Pressa", 0.66),
        ("Preço com Extrema Pressa e Desespero", 0.50),
    ],
}


def _parse_price(s: str) -> float:
    s = s.strip().replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _read_input(path: Path) -> tuple[str, float, float]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if len(lines) < 3:
        raise ValueError("O arquivo precisa conter 3 linhas: nome do produto, preço novo, preço usado.")
    name = lines[0]
    p1 = _parse_price(lines[1])
    p2 = _parse_price(lines[2])
    if p1 <= 0 or p2 <= 0:
        raise ValueError("Os preços precisam ser positivos.")
    return name, p1, p2


def _fmt_money(v: float) -> str:
    inteiro, frac = divmod(abs(v), 1)
    s_inteiro = f"{int(inteiro):,}".replace(",", ".")
    s_frac = f"{frac:.2f}".split(".")[1]
    return f"R$ {'-' if v < 0 else ''}{s_inteiro},{s_frac}"


def _format_block(grupo_rows, titulo_visivel: str):
    cat_w = max(len("Categoria"), *(len(r["Categoria"]) for r in grupo_rows))
    mult_w = max(len("Multiplicador"), *(len(f"{r['Multiplicador']:.2f}") for r in grupo_rows))
    preco_w = max(len("Preço Otimizado"), *(len(_fmt_money(r["Preço Otimizado"])) for r in grupo_rows))
    header_line = f"{'Categoria':<{cat_w}}  {'Multiplicador':>{mult_w}}  {'Preço Otimizado':>{preco_w}}"
    sep = "-" * len(header_line)
    lines = [titulo_visivel, header_line, sep]
    for r in grupo_rows:
        lines.append(
            f"{r['Categoria']:<{cat_w}}  {r['Multiplicador']:>{mult_w}.2f}  {_fmt_money(r['Preço Otimizado']):>{preco_w}}")
    return lines


def compute_rows(preco_novo: float, preco_usado: float):
    base_map = {"Produto Novo": preco_novo, "Produto Usado": preco_usado}
    rows: list[dict] = []
    for tipo, rules in RULES.items():
        base = base_map[tipo]
        rows.extend(
            {
                "Tipo": tipo,
                "Categoria": label,
                "Multiplicador": mult,
                "Preço Otimizado": round(base * mult, 2),
            }
            for label, mult in rules
        )
    return rows


def _build_output_lines(rows, produto: str) -> list[str]:
    all_lines = [f"Produto: {produto}", ""]
    for i, tipo in enumerate(["Produto Novo", "Produto Usado"]):
        grupo = [r for r in rows if r["Tipo"] == tipo]
        if not grupo:
            continue
        all_lines.extend(_format_block(grupo, tipo))
        if i == 0:
            all_lines.append("")
    return all_lines


def print_table(rows, produto: str) -> None:
    for line in _build_output_lines(rows, produto):
        print(line)


def save_png_table(rows, produto: str, output_path: Path) -> Path:
    all_lines = _build_output_lines(rows, produto)
    fontsize = 12
    line_height = 1.10
    left_pad_in = right_pad_in = top_pad_in = bottom_pad_in = 0.35
    max_chars = max((len(ln) for ln in all_lines), default=60)
    char_w_in = (fontsize / 72.0) * 0.60
    fig_w_in = left_pad_in + max_chars * char_w_in + right_pad_in
    line_h_in = (fontsize / 72.0) * line_height
    fig_h_in = top_pad_in + len(all_lines) * line_h_in + bottom_pad_in
    fig = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    step_y = line_h_in / fig_h_in
    y = 1.0 - (top_pad_in / fig_h_in)
    x = (left_pad_in / fig_w_in)
    for ln in all_lines:
        ax.text(x, y, ln, fontsize=fontsize, fontfamily="monospace", va="top", ha="left")
        y -= step_y
    fig.savefig(output_path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return output_path


def _slug_filename(name: str) -> str:
    norm = unicodedata.normalize("NFKD", name)
    ascii_only = norm.encode("ascii", "ignore").decode("ascii")
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in ascii_only.strip())
    safe = "_".join(filter(None, safe.split("_")))
    return safe or "produto"


def _output_dir() -> Path:
    script_dir = Path(__file__).resolve().parent
    out_dir = script_dir.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1]).expanduser()
    else:
        script_dir = Path(__file__).resolve().parent
        candidates = [Path(__file__).resolve().parent.parent / "input" / "product"]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            print(f"Arquivo de entrada não encontrado.\nCrie o arquivo relativo ao script:\n - {candidates[0]}")
            sys.exit(1)

    try:
        produto, preco_novo, preco_usado = _read_input(path)
    except Exception as e:
        print(f"Erro ao ler arquivo de entrada '{path}': {e}")
        sys.exit(1)

    rows = compute_rows(preco_novo, preco_usado)
    print_table(rows, produto)

    out_dir = _output_dir()
    base = f"preco_otimizado_{_slug_filename(produto)}"
    png_path = out_dir / f"{base}.png"
    txt_path = out_dir / f"{base}.txt"

    save_png_table(rows, produto, png_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(_build_output_lines(rows, produto)) + "\n")

    print(f"\nArquivos gerados:\n - {png_path.resolve()}\n - {txt_path.resolve()}")


if __name__ == "__main__":
    main()
