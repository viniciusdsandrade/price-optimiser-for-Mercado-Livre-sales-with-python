import sys
from pathlib import Path
import re
import matplotlib.pyplot as plt


def _parse_price(s: str) -> float:
    s = s.strip().replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _read_input(path: Path) -> tuple[str, float, float]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines() if ln.strip()]
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


def _clean_categoria(label: str) -> str:
    s = label.strip()
    s = re.sub(r"\s*0[,.]\d+x$", "", s)
    s = re.sub(r"^[A-Za-z]\s*-\s*", "", s)
    return s


def compute_rows(preco_novo: float, preco_usado: float):
    novo_rules = [
        ("1.A", "Produto (1) Novo", "A - Preço Competitivo 0,95x", 0.95),
        ("1.B", "Produto (1) Novo", "B - Preço Muito Competitivo 0,87x", 0.87),
        ("1.C", "Produto (1) Novo", "C - Preço Extremamente Competitivo 0,75x", 0.75),
        ("1.D", "Produto (1) Novo", "D - Preço com Pressa Moderada 0,62x", 0.62),
        ("1.E", "Produto (1) Novo", "E - Preço com Muita Pressa 0,49x", 0.49),
        ("1.F", "Produto (1) Novo", "F - Preço com Extrema Pressa e Desespero Moderado 0,4x", 0.40),
        ("1.G", "Produto (1) Novo", "G - Preço com Extrema Pressa e Extremo Desespero 0,3333x", 0.3333),
    ]
    usado_rules = [
        ("2.A", "Produto (2) Usado", "A - Preço Muito Competitivo 0,95x", 0.95),
        ("2.B", "Produto (2) Usado", "B - Preço Extremamente competitivo 0,85x", 0.85),
        ("2.C", "Produto (2) Usado", "C - Preço com Moderada Pressa 0,75x", 0.75),
        ("2.D", "Produto (2) Usado", "D - Preço com Muita Pressa 0,66x", 0.66),
        ("2.E", "Produto (2) Usado", "E - Preço com Extrema Pressa e Desespero 0,50x", 0.50),
    ]
    rows = []
    for chave, tipo, categoria, mult in novo_rules:
        rows.append({
            "Chave": chave,
            "Tipo": tipo,
            "Categoria": _clean_categoria(categoria),
            "Multiplicador": mult,
            "Preço Otimizado": round(preco_novo * mult, 2),
        })
    for chave, tipo, categoria, mult in usado_rules:
        rows.append({
            "Chave": chave,
            "Tipo": tipo,
            "Categoria": _clean_categoria(categoria),
            "Multiplicador": mult,
            "Preço Otimizado": round(preco_usado * mult, 2),
        })
    rows.sort(key=lambda r: r["Chave"])
    return rows


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


def print_table(rows, produto: str):
    print(f"Produto: {produto}\n")
    titulo_map = {"Produto (1) Novo": "Produto Novo", "Produto (2) Usado": "Produto Usado"}
    for tipo in ["Produto (1) Novo", "Produto (2) Usado"]:
        grupo = [r for r in rows if r["Tipo"] == tipo]
        if not grupo:
            continue
        for line in _format_block(grupo, titulo_map[tipo]):
            print(line)
        print()


def save_png_table(rows, produto: str, output_path: Path = Path("precos_otimizados.png")) -> Path:
    titulo_map = {"Produto (1) Novo": "Produto Novo", "Produto (2) Usado": "Produto Usado"}
    all_lines = [f"Produto: {produto}", ""]
    for i, tipo in enumerate(["Produto (1) Novo", "Produto (2) Usado"]):
        grupo = [r for r in rows if r["Tipo"] == tipo]
        if not grupo:
            continue
        block = _format_block(grupo, titulo_map[tipo])
        all_lines.extend(block)
        if i == 0:
            all_lines.append("")
    fontsize = 12
    line_height = 1.10
    left_pad_in = 0.35
    right_pad_in = 0.35
    top_pad_in = 0.35
    bottom_pad_in = 0.35
    max_chars = max(len(ln) for ln in all_lines) if all_lines else 60
    char_w_in = (fontsize / 72.0) * 0.60
    text_w_in = max_chars * char_w_in
    fig_w_in = left_pad_in + text_w_in + right_pad_in
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


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1]).expanduser()
    else:
        script_dir = Path(__file__).resolve().parent
        candidates = [script_dir / "product"]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            print("Arquivo de entrada não encontrado.\nCrie o arquivo relativo ao script:\n - {}".format(candidates[0]))
            sys.exit(1)
    try:
        produto, preco_novo, preco_usado = _read_input(path)
    except Exception as e:
        print(f"Erro ao ler arquivo de entrada '{path}': {e}")
        sys.exit(1)
    rows = compute_rows(preco_novo, preco_usado)
    print_table(rows, produto)
    out = save_png_table(rows, produto)
    print(f"\nImagem gerada: {out.resolve()}")


if __name__ == "__main__":
    main()
