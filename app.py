import os
from pathlib import Path
import pickle

from flask import Flask, jsonify, render_template, request
import requests


BASE_DIR = Path(__file__).resolve().parent
MOVIES_PATH = BASE_DIR / "movie_list.pkl"
SIMILARITY_PATH = BASE_DIR / "similarity.pkl"
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
POSTER_FALLBACK = "/static/poster-placeholder.svg"


def load_artifacts():
    if not MOVIES_PATH.exists() or not SIMILARITY_PATH.exists():
        missing = []
        if not MOVIES_PATH.exists():
            missing.append(MOVIES_PATH.name)
        if not SIMILARITY_PATH.exists():
            missing.append(SIMILARITY_PATH.name)
        raise FileNotFoundError(f"Missing required model files: {', '.join(missing)}")

    with MOVIES_PATH.open("rb") as movie_file:
        movies_df = pickle.load(movie_file)

    with SIMILARITY_PATH.open("rb") as similarity_file:
        similarity_matrix = pickle.load(similarity_file)

    return movies_df, similarity_matrix


movies, similarity = load_artifacts()
movie_titles = sorted(movies["title"].dropna().astype(str).unique().tolist())

app = Flask(__name__)

def fetch_poster(movie_id):
    if not TMDB_API_KEY:
        return POSTER_FALLBACK

    try:
        url = (
            f"https://api.themoviedb.org/3/movie/{int(movie_id)}"
            f"?api_key={TMDB_API_KEY}&language=en-US"
        )
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        if not poster_path:
            return POSTER_FALLBACK
        return f"{TMDB_IMAGE_BASE}{poster_path}"
    except (requests.RequestException, ValueError, TypeError):
        return POSTER_FALLBACK



def recommend(movie_title, top_n=6):
    matched_indexes = movies.index[movies["title"] == movie_title].tolist()
    if not matched_indexes:
        return []

    movie_index = matched_indexes[0]
    distances = sorted(
        list(enumerate(similarity[movie_index])),
        reverse=True,
        key=lambda item: item[1],
    )

    recommendations = []
    for idx, _score in distances[1 : top_n + 1]:
        title = str(movies.iloc[idx]["title"])
        movie_id = movies.iloc[idx].get("movie_id")
        recommendations.append(
            {
                "title": title,
                "poster": fetch_poster(movie_id),
            }
        )
    return recommendations


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", movie_titles=movie_titles)


@app.route("/recommend", methods=["POST"])
def recommend_route():
    payload = request.get_json(silent=True) or {}
    movie_title = str(payload.get("movie", "")).strip()

    if not movie_title:
        return jsonify({"ok": False, "error": "Please enter a movie title."}), 400

    recommendations = recommend(movie_title)
    if not recommendations:
        return jsonify(
            {
                "ok": False,
                "error": "Movie not found. Try selecting a title from the list.",
            }
        ), 404

    return jsonify({"ok": True, "movie": movie_title, "recommendations": recommendations})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, port=port)
