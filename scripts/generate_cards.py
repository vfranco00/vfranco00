"""Gera os cards SVG do perfil a partir da API GraphQL do GitHub.

Substitui os serviços públicos (github-readme-stats etc.) que saíram do ar:
os cards são gerados pelo próprio workflow e publicados na branch `output`.

Uso:
    GITHUB_TOKEN=... python3 scripts/generate_cards.py vfranco00 dist/
    python3 scripts/generate_cards.py --sample vfranco00 dist/   # dados fictícios, sem rede

Saída (cada um em versão -dark e -light):
    stats-*.svg       números gerais (commits, PRs, stars, contribuições...)
    langs-*.svg       linguagens mais usadas, por bytes de código
    project-<repo>-*.svg  card de cada projeto em destaque
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import sys
import urllib.request
from pathlib import Path

# Projetos em destaque. A descrição do GitHub tem prioridade; o texto aqui é
# usado só quando o repositório está sem descrição.
FEATURED = {
    "Nutri_Agent": "Planejador nutricional com IA (Gemini): calcula calorias, entende ingredientes e gamifica a cozinha.",
    "DataCost-Governance": "Governança de custos de dados: visibilidade e controle sobre o gasto com infraestrutura.",
    "Detecao-de-Tumores-Cerebrais-IA": "Visão computacional para detecção de tumores cerebrais em imagens de ressonância.",
    "NutriPlanner": "Cardápio semanal automático por preferência alimentar, com lista de compras gerada.",
}

# Linguagens que não representam código escrito à mão e distorcem o ranking.
IGNORED_LANGS = {"Jupyter Notebook", "HTML", "CSS", "SCSS", "Dockerfile", "Shell", "Makefile", "Procfile"}

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "title": "#e6edf3",
        "text": "#c9d1d9",
        "muted": "#8b949e",
        "accent": "#38bdf8",
        "accent2": "#818cf8",
        "track": "#21262d",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "title": "#1f2328",
        "text": "#24292f",
        "muted": "#57606a",
        "accent": "#0284c7",
        "accent2": "#4f46e5",
        "track": "#eaeef2",
    },
}

FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"

# Ícones Octicons (16x16), MIT.
ICONS = {
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z",
    "issue": "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
    "fork": "M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z",
    "people": "M2 5.5a3.5 3.5 0 1 1 5.898 2.549 5.508 5.508 0 0 1 3.034 4.084.75.75 0 1 1-1.482.235 4 4 0 0 0-7.9 0 .75.75 0 0 1-1.482-.236A5.507 5.507 0 0 1 3.102 8.05 3.493 3.493 0 0 1 2 5.5ZM11 4a3.001 3.001 0 0 1 2.22 5.018 5.01 5.01 0 0 1 2.56 3.012.749.749 0 0 1-.885.954.752.752 0 0 1-.549-.514 3.507 3.507 0 0 0-2.522-2.372.75.75 0 0 1-.574-.73v-.352a.75.75 0 0 1 .416-.672A1.5 1.5 0 0 0 11 5.5.75.75 0 0 1 11 4Zm-5.5-.5a2 2 0 1 0-.001 3.999A2 2 0 0 0 5.5 3.5Z",
    "flame": "M9.533.753V.752c.217 2.385 1.463 3.626 2.653 4.81C13.37 6.74 14.498 7.863 14.498 10c0 3.5-3 6-6.5 6S1.5 13.512 1.5 10c0-1.298.536-2.56 1.425-3.286.376-.308.862 0 1.035.454C4.46 8.487 5.18 9.035 5.5 9.035c.5 0 .555-.574.282-1.27C4.996 5.778 5.283 3.137 9.533.753Z",
}


# --------------------------------------------------------------------------- #
# Coleta de dados
# --------------------------------------------------------------------------- #

def graphql(query: str, variables: dict, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]


def fetch(login: str, token: str) -> dict:
    base = graphql(
        """
        query($login: String!) {
          user(login: $login) {
            name
            createdAt
            followers { totalCount }
            pullRequests { totalCount }
            issues { totalCount }
            contributionsCollection { contributionYears }
            repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
              totalCount
              nodes {
                name
                stargazerCount
                forkCount
                languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                  edges { size node { name color } }
                }
              }
            }
          }
        }
        """,
        {"login": login},
        token,
    )["user"]

    # Uma consulta por ano: contributionsCollection limita o intervalo a 1 ano.
    years = base["contributionsCollection"]["contributionYears"]
    fields = []
    for y in years:
        fields.append(
            f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") {{'
            " totalCommitContributions restrictedContributionsCount"
            " contributionCalendar { totalContributions } }"
        )
    yearly = graphql(
        "query($login: String!) { user(login: $login) { " + " ".join(fields) + " } }",
        {"login": login},
        token,
    )["user"] if years else {}

    repo_fields = []
    for i, name in enumerate(FEATURED):
        repo_fields.append(
            f'r{i}: repository(owner: $login, name: "{name}") {{'
            " name description stargazerCount forkCount pushedAt"
            " primaryLanguage { name color } repositoryTopics(first: 4) { nodes { topic { name } } } }"
        )
    repos = graphql(
        "query($login: String!) { " + " ".join(repo_fields) + " }",
        {"login": login},
        token,
    ) if FEATURED else {}

    return {"user": base, "yearly": yearly, "featured": [r for r in repos.values() if r]}


def sample() -> dict:
    """Dados fictícios para pré-visualizar o layout sem rede."""
    langs = [("TypeScript", "#3178c6", 900_000), ("Python", "#3572A5", 520_000),
             ("Java", "#b07219", 260_000), ("JavaScript", "#f1e05a", 180_000),
             ("Kotlin", "#A97BFF", 60_000), ("ABAP", "#E8274B", 20_000)]
    return {
        "user": {
            "name": "Victor Franco",
            "followers": {"totalCount": 42},
            "pullRequests": {"totalCount": 87},
            "issues": {"totalCount": 23},
            "repositories": {"totalCount": 35, "nodes": [
                {"name": "x", "stargazerCount": 6, "forkCount": 3, "languages": {"edges": [
                    {"size": s, "node": {"name": n, "color": c}} for n, c, s in langs]}}
            ]},
        },
        "yearly": {
            "y2026": {"totalCommitContributions": 640, "restrictedContributionsCount": 120, "contributionCalendar": {"totalContributions": 812}},
            "y2025": {"totalCommitContributions": 410, "restrictedContributionsCount": 40, "contributionCalendar": {"totalContributions": 530}},
        },
        "featured": [
            {"name": n, "description": None, "stargazerCount": i, "forkCount": 0,
             "pushedAt": "2026-10-01T00:00:00Z",
             "primaryLanguage": {"name": l, "color": c}, "repositoryTopics": {"nodes": []}}
            for i, (n, (l, c)) in enumerate(zip(FEATURED, [("Python", "#3572A5"), ("TypeScript", "#3178c6"),
                                                           ("Jupyter Notebook", "#DA5B0B"), ("Java", "#b07219")]))
        ],
    }


# --------------------------------------------------------------------------- #
# Agregação
# --------------------------------------------------------------------------- #

def summarize(data: dict) -> dict:
    user = data["user"]
    repos = user["repositories"]["nodes"]
    yearly = data["yearly"]
    this_year = str(dt.date.today().year)

    langs: dict[str, dict] = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in IGNORED_LANGS:
                continue
            entry = langs.setdefault(name, {"size": 0, "color": edge["node"]["color"] or "#8b949e"})
            entry["size"] += edge["size"]

    year_now = yearly.get(f"y{this_year}", {})
    return {
        "name": user.get("name") or "",
        "stars": sum(r["stargazerCount"] for r in repos),
        "forks": sum(r["forkCount"] for r in repos),
        "repos": user["repositories"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "commits_total": sum(y["totalCommitContributions"] + y["restrictedContributionsCount"] for y in yearly.values()),
        "contrib_total": sum(y["contributionCalendar"]["totalContributions"] for y in yearly.values()),
        "contrib_year": year_now.get("contributionCalendar", {}).get("totalContributions", 0),
        "year": this_year,
        "langs": sorted(langs.items(), key=lambda kv: kv[1]["size"], reverse=True),
    }


# --------------------------------------------------------------------------- #
# Renderização
# --------------------------------------------------------------------------- #

def esc(s: str) -> str:
    return html.escape(s, quote=True)


def fmt(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def icon(name: str, x: float, y: float, color: str, size: int = 16) -> str:
    scale = size / 16
    return f'<path transform="translate({x} {y}) scale({scale})" fill="{color}" d="{ICONS[name]}"/>'


def frame(w: int, h: int, t: dict, body: str, title: str, style: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
  <title>{esc(title)}</title>
  <style>
    text {{ font-family: {FONT}; }}
    .h {{ fill: {t["title"]}; font-size: 17px; font-weight: 700; }}
    .l {{ fill: {t["text"]}; font-size: 13.5px; }}
    .m {{ fill: {t["muted"]}; font-size: 12px; }}
    .v {{ fill: {t["title"]}; font-size: 14px; font-weight: 700; font-family: {MONO}; }}
    .in {{ opacity: 0; animation: in .5s ease-out forwards; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .in {{ opacity: 1; }} }}
    {style}
  </style>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>
  {body}
</svg>
"""


def stats_card(s: dict, t: dict) -> str:
    w, h = 495, 200
    rows = [
        ("star", "Stars recebidas", s["stars"]),
        ("commit", "Commits (todos os anos)", s["commits_total"]),
        ("pr", "Pull requests", s["prs"]),
        ("issue", "Issues", s["issues"]),
        ("repo", "Repositórios públicos", s["repos"]),
    ]
    parts = [f'<text class="h" x="25" y="36">Estatísticas no GitHub</text>']
    for i, (ic, label, value) in enumerate(rows):
        y = 70 + i * 25
        parts.append(
            f'<g class="in" style="animation-delay:{0.1 + i * 0.12:.2f}s">'
            f'{icon(ic, 25, y - 12, t["accent"])}'
            f'<text class="l" x="50" y="{y}">{label}</text>'
            f'<text class="v" x="290" y="{y}" text-anchor="end">{fmt(value)}</text></g>'
        )

    # Anel com o total de contribuições do ano corrente.
    cx, cy, r = 395, 108, 50
    circ = 2 * 3.14159 * r
    goal = max(1000, ((s["contrib_year"] // 500) + 1) * 500)
    frac = min(1.0, s["contrib_year"] / goal)
    parts.append(f"""
  <defs><linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{t["accent"]}"/><stop offset="1" stop-color="{t["accent2"]}"/>
  </linearGradient></defs>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["track"]}" stroke-width="9"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#ring)" stroke-width="9" stroke-linecap="round"
          stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}" transform="rotate(-90 {cx} {cy})" class="ring"/>
  <text x="{cx}" y="{cy + 2}" text-anchor="middle" class="v" style="font-size:22px">{fmt(s["contrib_year"])}</text>
  <text x="{cx}" y="{cy + 20}" text-anchor="middle" class="m" style="font-size:10px">contribuições</text>
  <text x="{cx}" y="{cy + 75}" text-anchor="middle" class="m">em {s["year"]} · {fmt(s["contrib_total"])} no total</text>""")
    style = (f".ring {{ animation: ring 1.4s ease-out .3s forwards; }}"
             f" @keyframes ring {{ to {{ stroke-dashoffset: {circ * (1 - frac):.1f}; }} }}"
             f" @media (prefers-reduced-motion: reduce) {{ .ring {{ stroke-dashoffset: {circ * (1 - frac):.1f}; }} }}")
    return frame(w, h, t, "\n  ".join(parts), "Estatísticas no GitHub", style)


def langs_card(s: dict, t: dict, top: int = 6) -> str:
    w, h = 495, 200
    langs = s["langs"][:top]
    total = sum(v["size"] for _, v in langs) or 1
    parts = ['<text class="h" x="25" y="36">Linguagens mais usadas</text>',
             f'<clipPath id="bar"><rect x="25" y="54" width="{w - 50}" height="10" rx="5"/></clipPath>',
             f'<rect x="25" y="54" width="{w - 50}" height="10" rx="5" fill="{t["track"]}"/>']
    x = 25.0
    bar = []
    for name, v in langs:
        seg = (w - 50) * v["size"] / total
        bar.append(f'<rect x="{x:.1f}" y="54" width="{seg + 0.5:.1f}" height="10" fill="{v["color"]}"/>')
        x += seg
    parts.append(f'<g clip-path="url(#bar)" class="grow">{"".join(bar)}</g>')

    for i, (name, v) in enumerate(langs):
        col, row = i % 2, i // 2
        lx, ly = 25 + col * 230, 96 + row * 32
        pct = 100 * v["size"] / total
        parts.append(
            f'<g class="in" style="animation-delay:{0.3 + i * 0.1:.2f}s">'
            f'<circle cx="{lx + 6}" cy="{ly - 4}" r="6" fill="{v["color"]}"/>'
            f'<text class="l" x="{lx + 20}" y="{ly}">{esc(name)}</text>'
            f'<text class="m" x="{lx + 205}" y="{ly}" text-anchor="end">{pct:.1f}%</text></g>'
        )
    style = (".grow { transform-origin: 25px 59px; transform: scaleX(0); animation: grow 1.1s ease-out .1s forwards; }"
             " @keyframes grow { to { transform: scaleX(1); } }"
             " @media (prefers-reduced-motion: reduce) { .grow { transform: none; } }")
    return frame(w, h, t, "\n  ".join(parts), "Linguagens mais usadas", style)


def wrap(text: str, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines


def relative(iso: str) -> str:
    when = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (dt.datetime.now(dt.timezone.utc) - when).days
    if days < 1:
        return "hoje"
    if days < 30:
        return f"há {days} dia{'s' if days > 1 else ''}"
    if days < 365:
        m = days // 30
        return f"há {m} {'mês' if m == 1 else 'meses'}"
    y = days // 365
    return f"há {y} ano{'s' if y > 1 else ''}"


def project_card(repo: dict, t: dict) -> str:
    w, h = 400, 150
    desc = repo.get("description") or FEATURED.get(repo["name"], "")
    lines = wrap(desc, 52)[:3]
    if len(wrap(desc, 52)) > 3:
        lines[-1] = lines[-1].rstrip(".,; ") + "…"
    lang = repo.get("primaryLanguage") or {"name": "—", "color": t["muted"]}
    parts = [
        icon("repo", 22, 22, t["muted"]),
        f'<text x="46" y="35" style="fill:{t["accent"]};font-size:15px;font-weight:700">{esc(repo["name"].replace("_", " "))}</text>',
    ]
    for i, line in enumerate(lines):
        parts.append(f'<text class="m" x="22" y="{64 + i * 19}" style="font-size:12.5px">{esc(line)}</text>')
    y = 128
    meta = f'<circle cx="28" cy="{y - 4}" r="6" fill="{lang["color"] or t["muted"]}"/>' \
           f'<text class="m" x="40" y="{y}">{esc(lang["name"])}</text>'
    x = 50 + len(lang["name"]) * 7
    meta += icon("star", x, y - 12, t["muted"], 14) + f'<text class="m" x="{x + 19}" y="{y}">{repo["stargazerCount"]}</text>'
    x += 45
    meta += icon("fork", x, y - 12, t["muted"], 14) + f'<text class="m" x="{x + 19}" y="{y}">{repo["forkCount"]}</text>'
    meta += f'<text class="m" x="{w - 22}" y="{y}" text-anchor="end">atualizado {relative(repo["pushedAt"])}</text>'
    parts.append(meta)
    return frame(w, h, t, "\n  ".join(parts), f'{repo["name"]} — {desc}')


# --------------------------------------------------------------------------- #

def main(argv: list[str]) -> None:
    use_sample = "--sample" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    login, out = args[0], Path(args[1])
    out.mkdir(parents=True, exist_ok=True)

    if use_sample:
        data = sample()
    else:
        token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN não definido")
        data = fetch(login, token)

    s = summarize(data)
    for theme, t in THEMES.items():
        files = {
            f"stats-{theme}.svg": stats_card(s, t),
            f"langs-{theme}.svg": langs_card(s, t),
        }
        for repo in data["featured"]:
            files[f"project-{repo['name']}-{theme}.svg"] = project_card(repo, t)
        for fname, svg in files.items():
            (out / fname).write_text(svg, encoding="utf-8")
            print(out / fname)


if __name__ == "__main__":
    main(sys.argv[1:])
