import requests
import re
import json

# Configuración
BASE_URL = "https://cuevana.fo"
LOCALE = "es"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Límites
HERO_LIMIT = 6
SECTION_LIMIT = 10  # para carruseles del home

# Sesión con headers
session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": BASE_URL
})

def get_build_id():
    url = f"{BASE_URL}/no-existe"
    print(f"🔄 Obteniendo buildId desde {url} ...")
    resp = session.get(url, timeout=15)
    print(f"   Respuesta {resp.status_code}, longitud {len(resp.text)}")
    match = re.search(r'"buildId":"([^"]+)"', resp.text)
    if match:
        build_id = match.group(1)
        print(f"✅ buildId extraído: {build_id}")
        return build_id
    else:
        print("❌ No se encontró buildId")
        return None

def fetch_json(build_id, path):
    clean_path = path.strip('/')
    url = f"{BASE_URL}/_next/data/{build_id}/{LOCALE}/{clean_path}.json"
    print(f"🌐 Pidiendo: {url}")
    resp = session.get(url, timeout=15)
    if resp.status_code != 200:
        print(f"❌ Error {resp.status_code} en {url}")
        return None
    print(f"✅ JSON recibido, longitud: {len(resp.text)}")
    return resp.json()

def parse_heroes(json_data):
    movies = json_data.get("pageProps", {}).get("movies", [])
    heroes = []
    for item in movies[:HERO_LIMIT]:
        titles = item.get("titles", {})
        images = item.get("images", {})
        slug_obj = item.get("slug", {})
        hero = {
            "title": titles.get("name", ""),
            "synopsis": item.get("overview", "")[:200],
            "posterUrl": images.get("poster", ""),
            "backdropUrl": images.get("backdrop", images.get("poster", "")),
            "slug": slug_obj.get("name", ""),
            "tmdbId": item.get("TMDbId", "")
        }
        if hero["title"] and hero["posterUrl"]:
            heroes.append(hero)
    return heroes

def parse_movies(json_data, type_="movie", limit=SECTION_LIMIT):
    movies = json_data.get("pageProps", {}).get("movies", [])
    items = []
    for item in movies[:limit]:
        titles = item.get("titles", {})
        images = item.get("images", {})
        slug_obj = item.get("slug", {})
        movie = {
            "title": titles.get("name", ""),
            "posterUrl": images.get("poster", ""),
            "slug": slug_obj.get("name", ""),
            "type": type_,
            "tmdbId": item.get("TMDbId", "")
        }
        if movie["title"] and movie["posterUrl"]:
            items.append(movie)
    return items

def main():
    build_id = get_build_id()
    if not build_id:
        return

    # Héroes
    movie_hero_json = fetch_json(build_id, "/peliculas/top/semana")
    series_hero_json = fetch_json(build_id, "/series/top/semana")

    movie_hero = parse_heroes(movie_hero_json) if movie_hero_json else []
    series_hero = parse_heroes(series_hero_json) if series_hero_json else []

    print(f"🎬 Héroes películas: {len(movie_hero)}")
    print(f"📺 Héroes series: {len(series_hero)}")

    # Secciones de películas
    movie_sections = []
    # Estrenos
    estrenos_json = fetch_json(build_id, "/estrenos")
    if estrenos_json:
        items = parse_movies(estrenos_json, type_="movie", limit=SECTION_LIMIT)
        movie_sections.append({
            "title": "Estrenos",
            "type": "movie",
            "seeMoreSlug": "estrenos",
            "items": items
        })
        print(f"   Sección Estrenos: {len(items)} items")

    # Últimas películas
    pelis_json = fetch_json(build_id, "/peliculas")
    if pelis_json:
        items = parse_movies(pelis_json, type_="movie", limit=SECTION_LIMIT)
        movie_sections.append({
            "title": "Últimas publicadas",
            "type": "movie",
            "seeMoreSlug": "ultimas",
            "items": items
        })
        print(f"   Sección Últimas películas: {len(items)} items")

    # Secciones de series
    series_sections = []

    # Series últimas (base)
    series_json = fetch_json(build_id, "/series")
    if series_json:
        items = parse_movies(series_json, type_="series", limit=SECTION_LIMIT)
        series_sections.append({
            "title": "Últimas publicadas",
            "type": "series",
            "seeMoreSlug": "ultimas-series",
            "items": items
        })
        print(f"   Sección Series últimas: {len(items)} items")

    # Series estrenos
    series_estrenos_json = fetch_json(build_id, "/series/estrenos")
    if series_estrenos_json:
        items = parse_movies(series_estrenos_json, type_="series", limit=SECTION_LIMIT)
        series_sections.append({
            "title": "Estrenos",
            "type": "series",
            "seeMoreSlug": "estrenos-series",
            "items": items
        })
        print(f"   Sección Series estrenos: {len(items)} items")

    # Construir HomeData
    home = {
        "movieHero": movie_hero,
        "seriesHero": series_hero,
        "movieSections": movie_sections,
        "episodeSections": series_sections
    }

    # Guardar JSON
    with open("hom.json", "w", encoding="utf-8") as f:
        json.dump(home, f, ensure_ascii=False, indent=2)

    print("✅ hom.json generado correctamente")

if __name__ == "__main__":
    main()
